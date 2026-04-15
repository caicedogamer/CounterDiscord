import discord
from discord import app_commands
from discord.ext import commands
from bot.db import queries
from bot.charts import user_profile as user_profile_chart

class UserCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="user", description="View stats for a specific member")
    @app_commands.describe(member="The member to look up", days="Look back period in days (default 30)")
    async def user(self, interaction: discord.Interaction, member: discord.Member, days: int = 30):
        await interaction.response.defer()
        try:
            stats        = await queries.get_user_stats(interaction.guild_id, member.id, days=days)
            emoji_rows   = await queries.get_user_top_emojis(interaction.guild_id, member.id, days=days)
            sticker_rows = await queries.get_user_top_stickers(interaction.guild_id, member.id, days=days)
            word_rows    = await queries.get_user_top_words(interaction.guild_id, member.id, days=days)

            if stats["msg_count"] == 0 and not emoji_rows and not sticker_rows:
                await interaction.followup.send(f"No data found for **{member.display_name}** in the last {days} days.")
                return

            buf = await user_profile_chart.user_profile(
                display_name=member.display_name,
                avatar_url=str(member.display_avatar.url),
                stats=stats,
                emoji_rows=emoji_rows,
                sticker_rows=sticker_rows,
                word_rows=word_rows,
                days=days,
                guild=interaction.guild,
                guild_name=interaction.guild.name,
            )
            await interaction.followup.send(file=discord.File(buf, filename="user_profile.png"))

        except Exception as e:
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"Something went wrong: `{e}`")

async def setup(bot):
    await bot.add_cog(UserCommands(bot))
