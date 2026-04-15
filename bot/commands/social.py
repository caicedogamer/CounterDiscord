import discord
from discord import app_commands
from discord.ext import commands
from bot.db import queries
from bot.charts import graph

class SocialCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="social-graph", description="Visualize who interacts with who the most")
    @app_commands.describe(days="Look back period in days (default 30)")
    async def social_graph(self, interaction: discord.Interaction, days: int = 30):
        await interaction.response.defer()
        try:
            rows = await queries.get_interactions(interaction.guild_id, days=days)
            if not rows:
                await interaction.followup.send(
                    "No interaction data yet - the bot tracks replies and mentions as they happen."
                )
                return

            # Resolve user IDs to display names
            async def resolve(user_id):
                member = interaction.guild.get_member(int(user_id))
                if member:
                    return member.display_name
                try:
                    member = await interaction.guild.fetch_member(int(user_id))
                    return member.display_name
                except Exception:
                    return f"User {str(user_id)[-4:]}"

            edges = []
            for row in rows:
                from_name = await resolve(row["from_user"])
                to_name   = await resolve(row["to_user"])
                edges.append((from_name, to_name, row["count"]))

            buf = await graph.social_graph(
                edges=edges,
                title=f"{interaction.guild.name}  ·  Social Interaction Graph - Last {days} days",
            )

            if buf is None:
                await interaction.followup.send("Not enough data to build a graph yet.")
                return

            await interaction.followup.send(file=discord.File(buf, filename="social_graph.png"))

        except Exception as e:
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"Something went wrong: `{e}`")

async def setup(bot):
    await bot.add_cog(SocialCommands(bot))
