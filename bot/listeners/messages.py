import re
import discord
from discord.ext import commands
import emoji
from bot.db import queries

CUSTOM_EMOJI_RE = re.compile(r"<a?:([a-zA-Z0-9_]+):(\d+)>")

class MessageListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _should_track(self, message):
        if message.author.bot:
            return False
        if not message.guild:
            return False
        try:
            from bot.db.connection import get_pool
            pool = get_pool()
            if pool is None:
                return False
            config = await queries.get_guild_config(message.guild.id)
            ignored = config.get("ignored_channels", [])
            return message.channel.id not in ignored
        except Exception:
            return False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not await self._should_track(message):
            return

        try:
            await queries.insert_message(
                message_id=message.id,
                guild_id=message.guild.id,
                channel_id=message.channel.id,
                user_id=message.author.id,
                created_at=message.created_at,
            )

            content = message.content
            config = await queries.get_guild_config(message.guild.id)
            tracked_words = config.get("tracked_words", [])

            for word in tracked_words:
                if word.lower() in content.lower():
                    await queries.insert_word_hit(
                        guild_id=message.guild.id,
                        channel_id=message.channel.id,
                        user_id=message.author.id,
                        word=word.lower(),
                        hit_at=message.created_at,
                    )

            for match in CUSTOM_EMOJI_RE.finditer(content):
                await queries.insert_emoji_hit(
                    guild_id=message.guild.id,
                    channel_id=message.channel.id,
                    user_id=message.author.id,
                    emoji_id=match.group(2),
                    emoji_name=match.group(1),
                    context="message",
                    hit_at=message.created_at,
                )

            for em in emoji.emoji_list(content):
                raw = em["emoji"]
                try:
                    name = emoji.demojize(raw).strip(":")
                    if name == raw:
                        name = None
                except Exception:
                    name = None

                await queries.insert_emoji_hit(
                    guild_id=message.guild.id,
                    channel_id=message.channel.id,
                    user_id=message.author.id,
                    emoji_id=raw,
                    emoji_name=name,
                    context="message",
                    hit_at=message.created_at,
                )

            for sticker in message.stickers:
                await queries.insert_sticker_hit(
                    guild_id=message.guild.id,
                    channel_id=message.channel.id,
                    user_id=message.author.id,
                    sticker_id=sticker.id,
                    sticker_name=sticker.name,
                    hit_at=message.created_at,
                )

            # Track replies
            if message.reference and message.reference.resolved:
                ref = message.reference.resolved
                if isinstance(ref, discord.Message) and ref.author and not ref.author.bot:
                    if ref.author.id != message.author.id:
                        await queries.insert_interaction(
                            guild_id=message.guild.id,
                            channel_id=message.channel.id,
                            from_user=message.author.id,
                            to_user=ref.author.id,
                            hit_at=message.created_at,
                        )

            # Track mentions
            for mentioned in message.mentions:
                if not mentioned.bot and mentioned.id != message.author.id:
                    await queries.insert_interaction(
                        guild_id=message.guild.id,
                        channel_id=message.channel.id,
                        from_user=message.author.id,
                        to_user=mentioned.id,
                        hit_at=message.created_at,
                    )

        except Exception as e:
            import traceback
            traceback.print_exc()

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.guild:
            await queries.mark_message_deleted(message.id)

async def setup(bot):
    await bot.add_cog(MessageListener(bot))