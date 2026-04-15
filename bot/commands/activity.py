import discord
from discord import app_commands
from discord.ext import commands
from bot.db import queries
from bot.charts import heatmap

class ActivityCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="activity", description="Message activity heatmap")
    @app_commands.describe(days="Look back period in days (default 30)")
    async def activity(self, interaction: discord.Interaction, days: int = 30):
        await interaction.response.defer()

        rows = await queries.get_activity_heatmap(interaction.guild_id, days=days)
        if not rows:
            await interaction.followup.send("No data yet.")
            return

        buf = await heatmap.activity_heatmap(
            rows=rows,
            title=f"{interaction.guild.name}  ·  Activity Heatmap - Last {days} days"
        )
        await interaction.followup.send(file=discord.File(buf, filename="activity.png"))

async def setup(bot):
    await bot.add_cog(ActivityCommands(bot))