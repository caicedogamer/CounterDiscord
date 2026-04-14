import discord
from discord import app_commands
from discord.ext import commands
from bot.db import queries
from bot.charts import bar

class StatsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="leaderboard", description="Top message senders")
    @app_commands.describe(days="Look back period in days (default 30)", limit="Number of users to show (default 10)")
    async def leaderboard(self, interaction: discord.Interaction, days: int = 30, limit: int = 10):
        await interaction.response.defer()

        rows = await queries.get_leaderboard(interaction.guild_id, days=days, limit=limit)
        if not rows:
            await interaction.followup.send("No data yet.")
            return

        labels = []
        for row in rows:
            member = interaction.guild.get_member(row["user_id"])
            labels.append(member.display_name if member else f"User {row['user_id']}")
        counts = [row["msg_count"] for row in rows]

        buf = await bar.horizontal_bar(
            labels=labels,
            values=counts,
            title=f"Top Senders — Last {days} days",
            xlabel="Messages",
        )
        await interaction.followup.send(file=discord.File(buf, filename="leaderboard.png"))

    @app_commands.command(name="least-active", description="Members who sent the fewest messages (at least 1)")
    @app_commands.describe(days="Look back period in days (default 30)", limit="Number of users to show (default 10)")
    async def least_active(self, interaction: discord.Interaction, days: int = 30, limit: int = 10):
        await interaction.response.defer()

        rows = await queries.get_least_active(interaction.guild_id, days=days, limit=limit)
        if not rows:
            await interaction.followup.send("No data yet.")
            return

        labels = []
        for row in rows:
            member = interaction.guild.get_member(row["user_id"])
            labels.append(member.display_name if member else f"User {row['user_id']}")
        counts = [row["msg_count"] for row in rows]

        buf = await bar.horizontal_bar(
            labels=labels,
            values=counts,
            title=f"Least Active Members — Last {days} days",
            xlabel="Messages",
        )
        await interaction.followup.send(file=discord.File(buf, filename="least_active.png"))

async def setup(bot):
    await bot.add_cog(StatsCommands(bot))
