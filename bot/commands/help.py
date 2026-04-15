import discord
from discord import app_commands
from discord.ext import commands

class HelpCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="List all available commands")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="CounterDiscord — Command List",
            description="All commands support a `days` parameter to set the look-back period (default 30).",
            color=0x4f8ef7,
        )

        embed.add_field(name="Stats", value=(
            "`/leaderboard [days] [limit]` — Top message senders\n"
            "`/least-active [days] [limit]` — Members with fewest messages (min 1)\n"
            "`/activity [days]` — Message activity heatmap by day & hour\n"
            "`/vc-leaderboard [days] [limit]` — Most time spent in voice channels\n"
            "`/dashboard [days]` — Full server stats dashboard"
        ), inline=False)

        embed.add_field(name="Lookup", value=(
            "`/user <member> [days]` — Top emojis, stickers, words & stats for a member\n"
            "`/word <term> [days] [limit]` — Who uses a word or phrase the most\n"
            "`/emoji <emoji> [days] [limit]` — Who uses a specific emoji the most\n"
            "`/top-emojis [days] [limit]` — Most used emojis server-wide\n"
            "`/top-stickers [days] [limit]` — Most used stickers server-wide\n"
            "`/top-channels [days] [limit]` — Most active channels\n"
            "`/social-graph [days]` — Network graph of who interacts with who"
        ), inline=False)

        embed.add_field(name="ML Insights", value=(
            "`/predict-active` — Predict which members will be active today\n"
            "`/user-archetypes` — Cluster members by behavior (Power User, Lurker, etc.)\n"
            "`/activity-spikes` — Detect unusually high activity periods\n"
            "`/emoji-trends` — See which emojis are rising or falling in usage"
        ), inline=False)

        embed.add_field(name="Configuration", value=(
            "`/track-word <word>` — Add a word to the tracking list\n"
            "`/untrack-word <word>` — Remove a word from the tracking list\n"
            "`/ignore-channel <channel>` — Stop tracking a channel\n"
            "`/set-background <image>` — Set a custom background for the dashboard\n"
            "`/remove-background` — Remove the custom dashboard background"
        ), inline=False)

        embed.set_footer(text="Manage Server permission required for configuration commands.")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCommands(bot))
