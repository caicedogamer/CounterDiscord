import os
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from bot.ml.features import get_user_activity_features

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models")

FEATURE_COLS = [
    "total_messages", "active_days",
    "avg_messages_per_day", "weekend_ratio",
    "peak_hour", "vc_hours"
]

async def train_and_cluster(guild_id: int, days: int = 30, n_clusters: int = 5):
    df = await get_user_activity_features(guild_id, days)
    if df.empty or len(df) < n_clusters:
        return None

    X = df[FEATURE_COLS].fillna(0).values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df = df.copy()
    df["cluster"] = kmeans.fit_predict(X_scaled)

    # Label clusters by their dominant feature
    cluster_means = df.groupby("cluster")[FEATURE_COLS].mean()
    labels = {}
    for cluster_id in range(n_clusters):
        means = cluster_means.loc[cluster_id]
        if means["vc_hours"] > cluster_means["vc_hours"].mean() * 1.5:
            labels[cluster_id] = "Voice Regular"
        elif means["total_messages"] > cluster_means["total_messages"].mean() * 1.5:
            labels[cluster_id] = "Power User"
        elif means["weekend_ratio"] > 0.6:
            labels[cluster_id] = "Weekend Warrior"
        elif means["active_days"] < cluster_means["active_days"].mean() * 0.5:
            labels[cluster_id] = "Lurker"
        else:
            labels[cluster_id] = "Casual Chatter"

    df["archetype"] = df["cluster"].map(labels)

    os.makedirs(MODEL_PATH, exist_ok=True)
    joblib.dump((kmeans, scaler, labels), f"{MODEL_PATH}/{guild_id}_clusters.joblib")

    return df[["user_id", "cluster", "archetype", "total_messages",
               "active_days", "vc_hours"]]
