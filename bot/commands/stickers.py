import discord
from discord import app_commands
from discord.ext import commands
from bot.db import queries
from bot.charts import bar

class StickerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="top-stickers", description="Most used stickers in the server")
    @app_commands.describe(days="Look back period in days (default 30)")
    async def top_stickers(self, interaction: discord.Interaction, days: int = 30):
        await interaction.response.defer()
        try:
            rows = await queries.get_top_stickers(interaction.guild_id, days=days)
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

    @app_commands.command(name="sticker", description="See who uses a sticker the most")
    @app_commands.describe(sticker_id="The numeric ID of the sticker", days="Look back period in days (default 30)")
    async def sticker(self, interaction: discord.Interaction, sticker_id: str, days: int = 30):
        await interaction.response.defer()
        try:
            rows = await queries.get_sticker_top_users(interaction.guild_id, int(sticker_id), days=days)
            if not rows:
                await interaction.followup.send(f"No data for that sticker yet.")
                return

            labels = []
            for row in rows:
                member = interaction.guild.get_member(int(row["user_id"]))
                if member:
                    labels.append(member.display_name)
                else:
                    try:
                        member = await interaction.guild.fetch_member(int(row["user_id"]))
                        labels.append(member.display_name)
                    except Exception:
                        labels.append(f"User {str(row['user_id'])[-4:]}")

            values = [row["count"] for row in rows]

            buf = await bar.horizontal_bar(
                labels=labels,
                values=values,
                title=f"Sticker usage — Last {days} days",
                xlabel="Times Used",
            )
            await interaction.followup.send(
                content=f"Sticker `{sticker_id}` usage stats:",
                file=discord.File(buf, filename="sticker.png")
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"Something went wrong: `{e}`")

async def setup(bot):
    await bot.add_cog(StickerCommands(bot))
