import re
import discord
from discord import app_commands
from discord.ext import commands
import emoji as emoji_lib
from bot.db import queries
from bot.charts import bar

def format_emoji_label(guild, emoji_id, emoji_name):
    if emoji_id and emoji_id.isdigit():
        guild_emoji = discord.utils.get(guild.emojis, id=int(emoji_id))
        if guild_emoji:
            return f":{guild_emoji.name}:"
        elif emoji_name:
            return f":{emoji_name}:"
        else:
            return f":custom_{emoji_id[-4:]}:"
    try:
        name = emoji_lib.demojize(emoji_id).strip(":")
        if name == emoji_id:
            return emoji_id
        if len(name) > 20:
            name = name[:18] + ".."
        return f":{name}:"
    except Exception:
        return emoji_id

class EmojiCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="emoji", description="See who uses an emoji the most")
    @app_commands.describe(emoji="Paste the emoji directly or type its numeric ID", days="Look back period in days (default 30)", limit="Number of users to show (default 10)")
    async def emoji(self, interaction: discord.Interaction, emoji: str, days: int = 30, limit: int = 10):
        await interaction.response.defer()

        try:
            custom_match = re.search(r"<a?:([a-zA-Z0-9_]+):(\d+)>", emoji)
            if custom_match:
                emoji_name = custom_match.group(1)
                emoji_id   = custom_match.group(2)
            elif emoji.strip().isdigit():
                emoji_id   = emoji.strip()
                emoji_name = None
            elif emoji.startswith(":") and emoji.endswith(":"):
                emoji_name = emoji.strip(":")
                emoji_id   = None
            else:
                emoji_id   = emoji.strip()
                try:
                    name = emoji_lib.demojize(emoji_id).strip(":")
                    emoji_name = None if name == emoji_id else name
                except Exception:
                    emoji_name = None

            if emoji_id is None:
                rows = await queries.get_emoji_top_users_by_name(
                    interaction.guild_id, emoji_name, days=days, limit=limit
                )
            else:
                rows = await queries.get_emoji_top_users(
                    interaction.guild_id, emoji_id, days=days, limit=limit
                )
                if not rows and emoji_name:
                    rows = await queries.get_emoji_top_users_by_name(
                        interaction.guild_id, emoji_name, days=days, limit=limit
                    )

            if not rows:
                await interaction.followup.send(
                    f"No data for **{emoji}** yet — send it in chat first then try again."
                )
                return

            # Resolve member names properly
            labels = []
            for row in rows:
                member = interaction.guild.get_member(int(row["user_id"]))
                if member:
                    labels.append(member.display_name)
                else:
                    # Try fetching if not in cache
                    try:
                        member = await interaction.guild.fetch_member(int(row["user_id"]))
                        labels.append(member.display_name)
                    except Exception:
                        labels.append(f"User {str(row['user_id'])[-4:]}")

            values = [row["count"] for row in rows]

            # Build clean title using name not raw emoji
            if emoji_name:
                title = f":{emoji_name}: usage — Last {days} days"
            elif emoji_id and emoji_id.isdigit():
                guild_emoji = discord.utils.get(interaction.guild.emojis, id=int(emoji_id))
                title = f":{guild_emoji.name}: usage — Last {days} days" if guild_emoji else f":custom_{emoji_id[-4:]}: usage — Last {days} days"
            else:
                try:
                    name = emoji_lib.demojize(emoji_id).strip(":")
                    title = f":{name}: usage — Last {days} days"
                except Exception:
                    title = f"Emoji usage — Last {days} days"

            buf = await bar.horizontal_bar(
                labels=labels,
                values=values,
                title=title,
                xlabel="Times Used",
            )
            await interaction.followup.send(
                content=f"**{emoji}** usage stats:",
                file=discord.File(buf, filename="emoji.png")
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"Something went wrong: `{e}`")

async def setup(bot):
    await bot.add_cog(EmojiCommands(bot))