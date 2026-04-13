import discord
from discord import app_commands
from discord.ext import commands
from bot.db import queries

class ConfigCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="track-word", description="Add a word to the tracking list")
    @app_commands.describe(word="The word or phrase to track")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def track_word(self, interaction: discord.Interaction, word: str):
        config = await queries.get_guild_config(interaction.guild_id)
        words = config.get("tracked_words", [])
        if word.lower() in words:
            await interaction.response.send_message(f"**{word}** is already being tracked.", ephemeral=True)
            return
        words.append(word.lower())
        config["tracked_words"] = words
        await queries.update_guild_config(interaction.guild_id, config)
        await interaction.response.send_message(f"✅ Now tracking **{word}**", ephemeral=True)

    @app_commands.command(name="untrack-word", description="Remove a word from the tracking list")
    @app_commands.describe(word="The word to stop tracking")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def untrack_word(self, interaction: discord.Interaction, word: str):
        config = await queries.get_guild_config(interaction.guild_id)
        words = config.get("tracked_words", [])
        if word.lower() not in words:
            await interaction.response.send_message(f"**{word}** isn't being tracked.", ephemeral=True)
            return
        words.remove(word.lower())
        config["tracked_words"] = words
        await queries.update_guild_config(interaction.guild_id, config)
        await interaction.response.send_message(f"✅ Stopped tracking **{word}**", ephemeral=True)

    @app_commands.command(name="ignore-channel", description="Stop tracking a channel")
    @app_commands.describe(channel="The channel to ignore")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ignore_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        config = await queries.get_guild_config(interaction.guild_id)
        ignored = config.get("ignored_channels", [])
        if channel.id in ignored:
            await interaction.response.send_message(f"{channel.mention} is already ignored.", ephemeral=True)
            return
        ignored.append(channel.id)
        config["ignored_channels"] = ignored
        await queries.update_guild_config(interaction.guild_id, config)
        await interaction.response.send_message(f"✅ Now ignoring {channel.mention}", ephemeral=True)

    @track_word.error
    @untrack_word.error
    @ignore_channel.error
    async def config_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You need **Manage Server** permission to use this command.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ConfigCommands(bot))