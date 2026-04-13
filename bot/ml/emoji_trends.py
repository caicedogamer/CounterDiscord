import pandas as pd
from sklearn.linear_model import LinearRegression
from bot.db.connection import get_pool

async def predict_emoji_trends(guild_id: int, days: int = 30, top_n: int = 5):
    rows = await get_pool().fetch(
        """
        SELECT
            emoji_id, emoji_name,
            DATE_TRUNC('day', hit_at) as day,
            COUNT(*) as count
        FROM emoji_hits
        WHERE guild_id = $1
          AND hit_at >= NOW() - ($2 || ' days')::interval
        GROUP BY emoji_id, emoji_name, day
        ORDER BY emoji_id, day
        """,
        guild_id, str(days)
    )

    if not rows:
        return None

    df = pd.DataFrame([dict(r) for r in rows],
                      columns=["emoji_id", "emoji_name", "day", "count"])
    df["day"] = pd.to_datetime(df["day"])
    df["day_num"] = (df["day"] - df["day"].min()).dt.days

    results = []
    for emoji_id, group in df.groupby("emoji_id"):
        if len(group) < 5:
            continue

        X = group["day_num"].values.reshape(-1, 1)
        y = group["count"].values

        model = LinearRegression()
        model.fit(X, y)

        slope = model.coef_[0]
        avg = y.mean()
        trend = "rising" if slope > 0.5 else "falling" if slope < -0.5 else "stable"

        results.append({
            "emoji_id": emoji_id,
            "emoji_name": group["emoji_name"].iloc[0],
            "trend": trend,
            "slope": round(float(slope), 2),
            "avg_daily": round(float(avg), 1),
            "total": int(y.sum()),
        })

    results.sort(key=lambda x: abs(x["slope"]), reverse=True)
    return results[:top_n]
