import re
import discord
from discord import app_commands
from discord.ext import commands
import emoji as emoji_lib
from bot.db import queries
from bot.charts import dashboard

def format_emoji_label(guild, emoji_id, emoji_name):
    if emoji_id.isdigit():
        guild_emoji = discord.utils.get(guild.emojis, id=int(emoji_id))
        if guild_emoji:
            return f":{guild_emoji.name}:"
        elif emoji_name:
            return f":{emoji_name}:"
        else:
            return f":custom_{emoji_id[-4:]}:"
    try:
        name = emoji_lib.demojize(emoji_id).strip(":")
        if len(name) > 20:
            name = name[:18] + ".."
        return f":{name}:"
    except Exception:
        return emoji_id

class DashboardCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dashboard", description="Full server stats dashboard")
    @app_commands.describe(days="Look back period in days (default 30)")
    async def server_dashboard(self, interaction: discord.Interaction, days: int = 30):
        await interaction.response.defer()

        leaderboard_rows = await queries.get_leaderboard(interaction.guild_id, days=days, limit=5)
        heatmap_rows     = await queries.get_activity_heatmap(interaction.guild_id, days=days)
        emoji_rows       = await queries.get_top_emojis(interaction.guild_id, days=days, limit=7)
        vc_rows          = await queries.get_vc_leaderboard(interaction.guild_id, days=days, limit=5)
        sticker_rows     = await queries.get_top_stickers(interaction.guild_id, days=days, limit=5)
        channel_rows     = await queries.get_top_channels(interaction.guild_id, days=days, limit=5)

        if not leaderboard_rows and not heatmap_rows:
            await interaction.followup.send("No data yet.")
            return

        board_data = []
        for row in leaderboard_rows:
            member = interaction.guild.get_member(row["user_id"])
            name = member.display_name if member else f"User {row['user_id']}"
            board_data.append({"name": name, "count": row["msg_count"]})

        emoji_data = []
        for row in emoji_rows:
            label = format_emoji_label(interaction.guild, row["emoji_id"], row["emoji_name"])
            emoji_data.append({"name": label, "count": row["count"]})

        vc_data = []
        for row in vc_rows:
            member = interaction.guild.get_member(row["user_id"])
            name = member.display_name if member else f"User {row['user_id']}"
            total = row["total_seconds"]
            hours = total // 3600
            minutes = (total % 3600) // 60
            vc_data.append({"name": name, "count": round(total / 3600, 4), "label": f"{hours}h {minutes}m"})

        sticker_data = []
        for row in sticker_rows:
            name = row["sticker_name"] or f"Sticker {str(row['sticker_id'])[-4:]}"
            sticker_data.append({"name": name, "count": row["count"]})

        channel_data = []
        for row in channel_rows:
            channel = interaction.guild.get_channel(int(row["channel_id"]))
            name = f"#{channel.name}" if channel else f"Channel {str(row['channel_id'])[-4:]}"
            channel_data.append({"name": name, "count": row["msg_count"]})

        buf = await dashboard.server_dashboard(
            leaderboard_rows=board_data,
            heatmap_rows=heatmap_rows,
            emoji_rows=emoji_data,
            vc_rows=vc_data,
            sticker_rows=sticker_data,
            channel_rows=channel_data,
            days=days,
        )
        await interaction.followup.send(file=discord.File(buf, filename="dashboard.png"))

async def setup(bot):
    await bot.add_cog(DashboardCommands(bot))