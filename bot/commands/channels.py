import discord
from discord import app_commands
from discord.ext import commands
from bot.db import queries
from bot.charts import bar

class ChannelCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="top-channels", description="Most active channels in the server")
    @app_commands.describe(days="Look back period in days (default 30)", limit="Number of channels to show (default 10)")
    async def top_channels(self, interaction: discord.Interaction, days: int = 30, limit: int = 10):
        await interaction.response.defer()
        try:
            rows = await queries.get_top_channels(interaction.guild_id, days=days, limit=limit)
            if not rows:
                await interaction.followup.send("No channel data yet.")
                return

            labels = []
            for row in rows:
                cid = int(row["channel_id"])
                channel = interaction.guild.get_channel(cid) or interaction.guild.get_thread(cid)
                labels.append(f"#{channel.name}" if channel else f"Channel {str(row['channel_id'])[-4:]}")
            values = [row["msg_count"] for row in rows]

            buf = await bar.horizontal_bar(
                labels=labels,
                values=values,
                title=f"{interaction.guild.name}  ·  Most Active Channels - Last {days} days",
                xlabel="Messages",
            )
            await interaction.followup.send(file=discord.File(buf, filename="top_channels.png"))
        except Exception as e:
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"Something went wrong: `{e}`")

async def setup(bot):
    await bot.add_cog(ChannelCommands(bot))
