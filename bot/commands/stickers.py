import discord
from discord import app_commands
from discord.ext import commands
from bot.db import queries
from bot.charts import bar

class StickerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="top-stickers", description="Most used stickers in the server")
    @app_commands.describe(days="Look back period in days (default 30)", limit="Number of stickers to show (default 10)")
    async def top_stickers(self, interaction: discord.Interaction, days: int = 30, limit: int = 10):
        await interaction.response.defer()
        try:
            rows = await queries.get_top_stickers(interaction.guild_id, days=days, limit=limit)
            if not rows:
                await interaction.followup.send("No sticker data yet.")
                return

            labels = [row["sticker_name"] or f"Sticker {str(row['sticker_id'])[-4:]}" for row in rows]
            values = [row["count"] for row in rows]

            buf = await bar.horizontal_bar(
                labels=labels,
                values=values,
                title=f"Top Stickers — Last {days} days",
                xlabel="Times Used",
            )
            await interaction.followup.send(file=discord.File(buf, filename="top_stickers.png"))
        except Exception as e:
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"Something went wrong: `{e}`")


async def setup(bot):
    await bot.add_cog(StickerCommands(bot))
