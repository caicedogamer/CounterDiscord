import asyncpg
from bot.config import DATABASE_URL

_pool = None

async def init_db_pool():
    global _pool
    _pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)

def get_pool() -> asyncpg.Pool:
    return _pool