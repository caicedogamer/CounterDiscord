import pandas as pd
from sklearn.ensemble import IsolationForest
from bot.db.connection import get_pool

async def detect_activity_spikes(guild_id: int, days: int = 30):
    rows = await get_pool().fetch(
        """
        SELECT
            DATE_TRUNC('hour', created_at) as hour,
            COUNT(*) as message_count
        FROM messages
        WHERE guild_id = $1
          AND created_at >= NOW() - ($2 || ' days')::interval
          AND is_deleted = FALSE
        GROUP BY hour
        ORDER BY hour
        """,
        guild_id, str(days)
    )

    if len(rows) < 48:
        return None

    df = pd.DataFrame([dict(r) for r in rows], columns=["hour", "message_count"])
    df["hour_of_day"] = pd.to_datetime(df["hour"]).dt.hour
    df["day_of_week"] = pd.to_datetime(df["hour"]).dt.dayofweek

    X = df[["message_count", "hour_of_day", "day_of_week"]].values

    model = IsolationForest(contamination=0.05, random_state=42)
    df = df.copy()
    df["anomaly"] = model.fit_predict(X)
    df["is_spike"] = df["anomaly"] == -1

    spikes = df[df["is_spike"]].copy()
    std = df["message_count"].std()
    if std == 0:
        return []
    spikes["z_score"] = (
        (spikes["message_count"] - df["message_count"].mean()) / std
    )
    spikes = spikes[spikes["z_score"] > 0]  # only positive spikes

    return spikes[["hour", "message_count", "z_score"]].to_dict("records")
