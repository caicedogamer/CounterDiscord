import discord
from discord.ext import commands
from datetime import datetime, timezone
from bot.db import queries
import emoji as emoji_lib

class ReactionListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if not payload.guild_id:
            return

        em = payload.emoji
        if em.id:
            # Custom emoji
            emoji_id = str(em.id)
            emoji_name = em.name
        else:
            # Standard unicode emoji
            emoji_id = str(em)
            emoji_name = emoji_lib.demojize(str(em)).strip(":")

        await queries.insert_emoji_hit(
            guild_id=payload.guild_id,
            channel_id=payload.channel_id,
            user_id=payload.user_id,
            emoji_id=emoji_id,
            emoji_name=emoji_name,
            context="reaction",
            hit_at=datetime.now(timezone.utc),
        )

async def setup(bot):
    await bot.add_cog(ReactionListener(bot))