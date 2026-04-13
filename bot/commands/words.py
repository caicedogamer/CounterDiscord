import discord
from discord import app_commands
from discord.ext import commands
from bot.db import queries
from bot.charts import bar

class WordCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="word", description="See who uses a word the most")
    @app_commands.describe(term="The word or phrase to look up", days="Look back period in days (default 30)")
    async def word(self, interaction: discord.Interaction, term: str, days: int = 30):
        await interaction.response.defer()

        try:
            rows = await queries.get_word_top_users(interaction.guild_id, term, days=days)
            if not rows:
                await interaction.followup.send(
                    f"No data for **{term}** yet. Make sure it's being tracked with `/track-word`."
                )
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
                title=f'"{term}" usage — Last {days} days',
                xlabel="Times Used",
            )
            await interaction.followup.send(
                content=f"**{term}** usage stats:",
                file=discord.File(buf, filename="word.png")
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"Something went wrong: `{e}`")

async def setup(bot):
    await bot.add_cog(WordCommands(bot))
