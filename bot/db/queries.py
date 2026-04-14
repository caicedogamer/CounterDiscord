from bot.db.connection import get_pool
import json

async def insert_message(message_id, guild_id, channel_id, user_id, created_at):
    await get_pool().execute(
        """INSERT INTO messages (message_id, guild_id, channel_id, user_id, created_at)
           VALUES ($1, $2, $3, $4, $5) ON CONFLICT DO NOTHING""",
        message_id, guild_id, channel_id, user_id, created_at
    )

async def mark_message_deleted(message_id):
    await get_pool().execute(
        "UPDATE messages SET is_deleted = TRUE WHERE message_id = $1",
        message_id
    )

async def insert_word_hit(guild_id, channel_id, user_id, word, hit_at):
    await get_pool().execute(
        """INSERT INTO word_hits (guild_id, channel_id, user_id, word, hit_at)
           VALUES ($1, $2, $3, $4, $5)""",
        guild_id, channel_id, user_id, word, hit_at
    )

async def insert_emoji_hit(guild_id, channel_id, user_id, emoji_id, emoji_name, context, hit_at):
    try:
        await get_pool().execute(
            """INSERT INTO emoji_hits (guild_id, channel_id, user_id, emoji_id, emoji_name, context, hit_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            guild_id, channel_id, user_id, emoji_id, emoji_name, context, hit_at
        )
    except Exception as e:
        import traceback
        traceback.print_exc()

async def get_guild_config(guild_id):
    row = await get_pool().fetchrow(
        "SELECT config FROM guild_config WHERE guild_id = $1",
        guild_id
    )
    if not row:
        return {}
    config = row["config"]
    if isinstance(config, dict):
        return config
    if isinstance(config, str):
        return json.loads(config)
    return {}

async def update_guild_config(guild_id, config):
    await get_pool().execute(
        """INSERT INTO guild_config (guild_id, config) VALUES ($1, $2)
           ON CONFLICT (guild_id) DO UPDATE SET config = $2""",
        guild_id, json.dumps(config)
    )

async def get_leaderboard(guild_id, days=30, limit=10):
    return await get_pool().fetch(
        """SELECT user_id, COUNT(*) as msg_count
           FROM messages
           WHERE guild_id = $1
             AND created_at >= NOW() - ($2 || ' days')::interval
             AND is_deleted = FALSE
           GROUP BY user_id
           ORDER BY msg_count DESC
           LIMIT $3""",
        guild_id, str(days), limit
    )

async def get_activity_heatmap(guild_id, channel_id=None, days=30):
    if channel_id:
        return await get_pool().fetch(
            """SELECT
                 EXTRACT(DOW FROM created_at AT TIME ZONE 'UTC') AS day_of_week,
                 EXTRACT(HOUR FROM created_at AT TIME ZONE 'UTC') AS hour_of_day,
                 COUNT(*) AS msg_count
               FROM messages
               WHERE guild_id = $1
                 AND created_at >= NOW() - ($2 || ' days')::interval
                 AND channel_id = $3
               GROUP BY day_of_week, hour_of_day""",
            guild_id, str(days), channel_id
        )
    else:
        return await get_pool().fetch(
            """SELECT
                 EXTRACT(DOW FROM created_at AT TIME ZONE 'UTC') AS day_of_week,
                 EXTRACT(HOUR FROM created_at AT TIME ZONE 'UTC') AS hour_of_day,
                 COUNT(*) AS msg_count
               FROM messages
               WHERE guild_id = $1
                 AND created_at >= NOW() - ($2 || ' days')::interval
               GROUP BY day_of_week, hour_of_day""",
            guild_id, str(days)
        )

async def get_word_frequency(guild_id, word, days=30):
    return await get_pool().fetch(
        """SELECT DATE_TRUNC('day', hit_at) as day, COUNT(*) as count
           FROM word_hits
           WHERE guild_id = $1 AND word = $2
             AND hit_at >= NOW() - ($3 || ' days')::interval
           GROUP BY day ORDER BY day""",
        guild_id, word.lower(), str(days)
    )

async def get_word_top_users(guild_id, word, days=30, limit=10):
    return await get_pool().fetch(
        """SELECT user_id, COUNT(*) as count
           FROM word_hits
           WHERE guild_id = $1 AND word = $2
             AND hit_at >= NOW() - ($3 || ' days')::interval
           GROUP BY user_id
           ORDER BY count DESC
           LIMIT $4""",
        guild_id, word.lower(), str(days), limit
    )

async def get_emoji_top_users(guild_id, emoji_id, days=30, limit=10):
    return await get_pool().fetch(
        """SELECT user_id, COUNT(*) as count
           FROM emoji_hits
           WHERE guild_id = $1 AND emoji_id = $2
             AND hit_at >= NOW() - ($3 || ' days')::interval
           GROUP BY user_id
           ORDER BY count DESC
           LIMIT $4""",
        guild_id, emoji_id, str(days), limit
    )

async def get_emoji_top_users_by_name(guild_id, emoji_name, days=30, limit=10):
    return await get_pool().fetch(
        """SELECT user_id, COUNT(*) as count
           FROM emoji_hits
           WHERE guild_id = $1
             AND LOWER(emoji_name) = LOWER($2)
             AND hit_at >= NOW() - ($3 || ' days')::interval
           GROUP BY user_id
           ORDER BY count DESC
           LIMIT $4""",
        guild_id, emoji_name, str(days), limit
    )

async def get_top_emojis(guild_id, days=30, limit=10):
    return await get_pool().fetch(
        """SELECT emoji_id, emoji_name, COUNT(*) as count
           FROM emoji_hits
           WHERE guild_id = $1
             AND hit_at >= NOW() - ($2 || ' days')::interval
           GROUP BY emoji_id, emoji_name
           ORDER BY count DESC
           LIMIT $3""",
        guild_id, str(days), limit
    )

async def get_vc_leaderboard(guild_id, days=30, limit=5):
    return await get_pool().fetch(
        """SELECT user_id, SUM(duration_seconds) as total_seconds
           FROM vc_sessions
           WHERE guild_id = $1
             AND joined_at >= NOW() - ($2 || ' days')::interval
           GROUP BY user_id
           ORDER BY total_seconds DESC
           LIMIT $3""",
        guild_id, str(days), limit
    )

async def insert_sticker_hit(guild_id, channel_id, user_id, sticker_id, sticker_name, hit_at):
    await get_pool().execute(
        """INSERT INTO sticker_hits (guild_id, channel_id, user_id, sticker_id, sticker_name, hit_at)
           VALUES ($1, $2, $3, $4, $5, $6)""",
        guild_id, channel_id, user_id, sticker_id, sticker_name, hit_at
    )

async def get_top_stickers(guild_id, days=30, limit=10):
    return await get_pool().fetch(
        """SELECT sticker_id, sticker_name, COUNT(*) as count
           FROM sticker_hits
           WHERE guild_id = $1
             AND hit_at >= NOW() - ($2 || ' days')::interval
           GROUP BY sticker_id, sticker_name
           ORDER BY count DESC
           LIMIT $3""",
        guild_id, str(days), limit
    )

async def get_sticker_top_users(guild_id, sticker_id, days=30, limit=10):
    return await get_pool().fetch(
        """SELECT user_id, COUNT(*) as count
           FROM sticker_hits
           WHERE guild_id = $1 AND sticker_id = $2
             AND hit_at >= NOW() - ($3 || ' days')::interval
           GROUP BY user_id
           ORDER BY count DESC
           LIMIT $4""",
        guild_id, sticker_id, str(days), limit
    )

async def get_least_active(guild_id, days=30, limit=10):
    return await get_pool().fetch(
        """SELECT user_id, COUNT(*) as msg_count
           FROM messages
           WHERE guild_id = $1
             AND created_at >= NOW() - ($2 || ' days')::interval
             AND is_deleted = FALSE
           GROUP BY user_id
           HAVING COUNT(*) >= 1
           ORDER BY msg_count ASC
           LIMIT $3""",
        guild_id, str(days), limit
    )

async def get_top_channels(guild_id, days=30, limit=10):
    return await get_pool().fetch(
        """SELECT channel_id, COUNT(*) as msg_count
           FROM messages
           WHERE guild_id = $1
             AND created_at >= NOW() - ($2 || ' days')::interval
             AND is_deleted = FALSE
           GROUP BY channel_id
           ORDER BY msg_count DESC
           LIMIT $3""",
        guild_id, str(days), limit
    )

async def insert_interaction(guild_id, channel_id, from_user, to_user, hit_at):
    await get_pool().execute(
        """INSERT INTO user_interactions (guild_id, channel_id, from_user, to_user, hit_at)
           VALUES ($1, $2, $3, $4, $5)""",
        guild_id, channel_id, from_user, to_user, hit_at
    )

async def get_interactions(guild_id, days=30, limit=50):
    return await get_pool().fetch(
        """SELECT from_user, to_user, COUNT(*) as count
           FROM user_interactions
           WHERE guild_id = $1
             AND hit_at >= NOW() - ($2 || ' days')::interval
           GROUP BY from_user, to_user
           ORDER BY count DESC
           LIMIT $3""",
        guild_id, str(days), limit
    )

async def insert_vc_session(guild_id, channel_id, user_id, joined_at, left_at, duration_seconds):
    await get_pool().execute(
        """INSERT INTO vc_sessions (guild_id, channel_id, user_id, joined_at, left_at, duration_seconds)
           VALUES ($1, $2, $3, $4, $5, $6)""",
        guild_id, channel_id, user_id, joined_at, left_at, duration_seconds
    )