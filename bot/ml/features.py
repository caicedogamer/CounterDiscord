import pandas as pd
from bot.db.connection import get_pool

async def get_user_activity_features(guild_id: int, days: int = 30) -> pd.DataFrame:
    """
    Build a feature matrix with one row per user.
    Features: message count, active days, avg messages/day,
              peak hour, weekend ratio, emoji usage rate, vc hours.
    """
    rows = await get_pool().fetch(
        """
        SELECT
            user_id,
            COUNT(*) as total_messages,
            COUNT(DISTINCT DATE(created_at)) as active_days,
            EXTRACT(DOW FROM created_at) as day_of_week,
            EXTRACT(HOUR FROM created_at) as hour
        FROM messages
        WHERE guild_id = $1
          AND created_at >= NOW() - ($2 || ' days')::interval
          AND is_deleted = FALSE
        GROUP BY user_id, day_of_week, hour
        """,
        guild_id, str(days)
    )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame([dict(r) for r in rows],
                      columns=["user_id", "total_messages", "active_days",
                               "day_of_week", "hour"])

    # Aggregate per user
    features = df.groupby("user_id").agg(
        total_messages=("total_messages", "sum"),
        active_days=("active_days", "max"),
        peak_hour=("hour", lambda x: x.mode()[0] if len(x) > 0 else 0),
        weekend_ratio=("day_of_week", lambda x: (x.isin([0, 6])).mean()),
    ).reset_index()

    features["avg_messages_per_day"] = (
        features["total_messages"] / features["active_days"].replace(0, 1)
    )

    # Add VC hours
    vc_rows = await get_pool().fetch(
        """
        SELECT user_id, COALESCE(SUM(duration_seconds), 0) as total_vc_seconds
        FROM vc_sessions
        WHERE guild_id = $1
          AND joined_at >= NOW() - ($2 || ' days')::interval
        GROUP BY user_id
        """,
        guild_id, str(days)
    )
    vc_df = pd.DataFrame([dict(r) for r in vc_rows],
                         columns=["user_id", "total_vc_seconds"]) if vc_rows else pd.DataFrame(columns=["user_id", "total_vc_seconds"])
    vc_df["vc_hours"] = vc_df["total_vc_seconds"] / 3600

    features = features.merge(vc_df[["user_id", "vc_hours"]], on="user_id", how="left")
    features["vc_hours"] = features["vc_hours"].fillna(0)

    return features
