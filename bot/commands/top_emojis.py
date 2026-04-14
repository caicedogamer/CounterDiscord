import re
import discord
from discord import app_commands
from discord.ext import commands
import emoji as emoji_lib
from bot.db import queries
from bot.charts import bar

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

class TopEmojiCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="top-emojis", description="Most used emojis in the server")
    @app_commands.describe(days="Look back period in days (default 30)", limit="Number of emojis to show (default 10)")
    async def top_emojis(self, interaction: discord.Interaction, days: int = 30, limit: int = 10):
        await interaction.response.defer()

        rows = await queries.get_top_emojis(interaction.guild_id, days=days, limit=limit)
        if not rows:
            await interaction.followup.send("No emoji data yet.")
            return

        labels = []
        for row in rows:
            label = format_emoji_label(interaction.guild, row["emoji_id"], row["emoji_name"])
            labels.append(label)
        values = [row["count"] for row in rows]

        buf = await bar.horizontal_bar(
            labels=labels,
            values=values,
            title=f"Top Emojis — Last {days} days",
            xlabel="Times Used",
        )
        await interaction.followup.send(file=discord.File(buf, filename="top_emojis.png"))

async def setup(bot):
    await bot.add_cog(TopEmojiCommands(bot))