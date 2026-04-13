import discord
from discord.ext import commands
from datetime import datetime, timezone
from bot.db import queries

class VoiceListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._active_sessions = {}  # (guild_id, user_id) -> joined_at

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ):
        if member.bot:
            return

        key = (member.guild.id, member.id)
        now = datetime.now(timezone.utc)

        # User joined a VC
        if before.channel is None and after.channel is not None:
            self._active_sessions[key] = (after.channel.id, now)

        # User left a VC
        elif before.channel is not None and after.channel is None:
            if key in self._active_sessions:
                channel_id, joined_at = self._active_sessions.pop(key)
                duration = int((now - joined_at).total_seconds())
                await queries.insert_vc_session(
                    guild_id=member.guild.id,
                    channel_id=channel_id,
                    user_id=member.id,
                    joined_at=joined_at,
                    left_at=now,
                    duration_seconds=duration,
                )

        # User switched channels
        elif before.channel is not None and after.channel is not None and before.channel != after.channel:
            if key in self._active_sessions:
                channel_id, joined_at = self._active_sessions.pop(key)
                duration = int((now - joined_at).total_seconds())
                await queries.insert_vc_session(
                    guild_id=member.guild.id,
                    channel_id=channel_id,
                    user_id=member.id,
                    joined_at=joined_at,
                    left_at=now,
                    duration_seconds=duration,
                )
            # Start new session in the new channel
            self._active_sessions[key] = (after.channel.id, now)

async def setup(bot):
    await bot.add_cog(VoiceListener(bot))