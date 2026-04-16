import os
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from bot.db.connection import get_pool
from bot.ml.features import get_user_activity_features

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models")

FEATURE_COLS = ["total_messages", "active_days", "avg_messages_per_day",
                "weekend_ratio", "peak_hour", "vc_hours"]

async def _build_training_data(guild_id: int):
    """
    For each user, check if they were active yesterday.
    Features are from the 7 days before that.
    Label = 1 if they sent any message yesterday, 0 otherwise.
    """
    rows = await get_pool().fetch(
        """
        WITH yesterday_active AS (
            SELECT DISTINCT user_id
            FROM messages
            WHERE guild_id = $1
              AND created_at >= NOW() - INTERVAL '1 day'
              AND created_at < NOW()
              AND is_deleted = FALSE
        ),
        all_users AS (
            SELECT DISTINCT user_id FROM messages WHERE guild_id = $1
        )
        SELECT
            a.user_id,
            CASE WHEN y.user_id IS NOT NULL THEN 1 ELSE 0 END as was_active
        FROM all_users a
        LEFT JOIN yesterday_active y ON a.user_id = y.user_id
        """,
        guild_id
    )

    if not rows:
        return None, None, None

    labels_df = pd.DataFrame([dict(r) for r in rows], columns=["user_id", "was_active"])
    features_df = await get_user_activity_features(guild_id, days=7)

    if features_df.empty:
        return None, None, None

    merged = features_df.merge(labels_df, on="user_id")

    X = merged[FEATURE_COLS].fillna(0).values
    y = merged["was_active"].values
    user_ids = merged["user_id"].values

    return X, y, user_ids


async def train_activity_model(guild_id: int) -> bool:
    X, y, _ = await _build_training_data(guild_id)
    if X is None:
        return False
    if len(X) < 20 or y.sum() < 5 or y.sum() == len(y):
        return False

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=6,
        random_state=42,
        class_weight="balanced"
    )
    model.fit(X_scaled, y)

    os.makedirs(MODEL_PATH, exist_ok=True)
    joblib.dump((model, scaler), f"{MODEL_PATH}/{guild_id}_activity.joblib")
    return True


async def predict_active_members(guild_id: int, top_n: int = 10):
    model_file = f"{MODEL_PATH}/{guild_id}_activity.joblib"
    if not os.path.exists(model_file):
        trained = await train_activity_model(guild_id)
        if not trained:
            return None

    model, scaler = joblib.load(model_file)
    features_df = await get_user_activity_features(guild_id, days=7)
    if features_df.empty:
        return None

    X = features_df[FEATURE_COLS].fillna(0).values
    X_scaled = scaler.transform(X)

    probs_matrix = model.predict_proba(X_scaled)
    if probs_matrix.shape[1] < 2:
        # Model was trained with only one class — delete it so it retrains next time
        os.remove(model_file)
        return None
    probs = probs_matrix[:, 1]
    features_df = features_df.copy()
    features_df["activity_probability"] = probs

    top = features_df.nlargest(top_n, "activity_probability")
    return top[["user_id", "activity_probability"]]
