import discord
from discord.ext import commands
import asyncio
from bot.config import DISCORD_TOKEN
from bot.db.connection import init_db_pool

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    await init_db_pool()
    await bot.load_extension("bot.listeners.messages")
    await bot.load_extension("bot.listeners.reactions")
    await bot.load_extension("bot.commands.stats")
    await bot.load_extension("bot.commands.activity")
    await bot.load_extension("bot.commands.dashboard")
    await bot.load_extension("bot.commands.words")
    await bot.load_extension("bot.commands.emojis")
    await bot.load_extension("bot.commands.config")
    await bot.load_extension("bot.commands.top_emojis")
    await bot.load_extension("bot.listeners.voice")
    await bot.load_extension("bot.commands.vc")
    await bot.load_extension("bot.commands.ml_insights")
    await bot.load_extension("bot.commands.stickers")
    await bot.load_extension("bot.commands.social")
    await bot.load_extension("bot.commands.channels")
    synced = await bot.tree.sync()
    print(f"Logged in as {bot.user} — synced {len(synced)} commands")

asyncio.run(bot.start(DISCORD_TOKEN))