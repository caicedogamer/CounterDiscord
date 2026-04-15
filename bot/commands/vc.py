import discord
from discord import app_commands
from discord.ext import commands
from bot.db import queries
from bot.charts import bar

class VCCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="vc-leaderboard", description="Who spends the most time in voice channels")
    @app_commands.describe(days="Look back period in days (default 30)", limit="Number of users to show (default 10)")
    async def vc_leaderboard(self, interaction: discord.Interaction, days: int = 30, limit: int = 10):
        await interaction.response.defer()

        rows = await queries.get_vc_leaderboard(interaction.guild_id, days=days, limit=limit)
        if not rows:
            await interaction.followup.send("No VC data yet.")
            return

        labels = []
        values = []
        bar_labels = []
        for row in rows:
            member = interaction.guild.get_member(row["user_id"])
            labels.append(member.display_name if member else f"User {row['user_id']}")
            total = row["total_seconds"]
            hours = total // 3600
            minutes = (total % 3600) // 60
            values.append(round(total / 3600, 4))
            bar_labels.append(f"{hours}h {minutes}m")

        buf = await bar.horizontal_bar(
            labels=labels,
            values=values,
            title=f"{interaction.guild.name}  ·  VC Time - Last {days} days",
            xlabel="Hours",
            bar_labels=bar_labels,
        )
        await interaction.followup.send(file=discord.File(buf, filename="vc.png"))

async def setup(bot):
    await bot.add_cog(VCCommands(bot))