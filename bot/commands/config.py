import os
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from bot.db import queries

BACKGROUNDS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "backgrounds")

def bg_path(guild_id):
    return os.path.join(BACKGROUNDS_DIR, f"{guild_id}.png")

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

    @app_commands.command(name="set-background", description="Set a custom background image for the dashboard")
    @app_commands.describe(image="Attach a PNG or JPG image")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_background(self, interaction: discord.Interaction, image: discord.Attachment):
        if not image.content_type or not image.content_type.startswith("image/"):
            await interaction.response.send_message("Please attach a valid image file (PNG or JPG).", ephemeral=True)
            return
        if image.size > 8 * 1024 * 1024:
            await interaction.response.send_message("Image must be under 8 MB.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        os.makedirs(BACKGROUNDS_DIR, exist_ok=True)
        path = bg_path(interaction.guild_id)
        async with aiohttp.ClientSession() as session:
            async with session.get(image.url) as resp:
                if resp.status != 200:
                    await interaction.followup.send("Failed to download the image.", ephemeral=True)
                    return
                data = await resp.read()
        with open(path, "wb") as f:
            f.write(data)
        await interaction.followup.send("✅ Dashboard background updated. Run `/dashboard` to see it.", ephemeral=True)

    @app_commands.command(name="remove-background", description="Remove the custom dashboard background")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def remove_background(self, interaction: discord.Interaction):
        path = bg_path(interaction.guild_id)
        if os.path.exists(path):
            os.remove(path)
            await interaction.response.send_message("✅ Custom background removed.", ephemeral=True)
        else:
            await interaction.response.send_message("No custom background is set.", ephemeral=True)

    @track_word.error
    @untrack_word.error
    @ignore_channel.error
    @set_background.error
    @remove_background.error
    async def config_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You need **Manage Server** permission to use this command.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ConfigCommands(bot))