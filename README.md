# CounterDiscord

A Discord analytics bot that tracks server activity, visualizes stats as charts, and uses machine learning to surface insights about your community.

---

## Features

- **Message tracking** — logs every message with soft-delete support and channel ignore lists
- **Emoji tracking** — tracks both custom and unicode emoji usage in messages and reactions
- **Voice tracking** — records VC session durations per user
- **Word tracking** — monitors configurable keywords and phrases
- **Sticker tracking** — tracks sticker usage per user and server-wide
- **Social graph** — visualizes who interacts with who via replies and mentions
- **Chart generation** — dark-themed charts rendered with matplotlib/seaborn
- **ML insights** — activity prediction, behavior clustering, anomaly detection, and emoji trend analysis

---

## Commands

### Stats
| Command | Description |
|---|---|
| `/leaderboard [days]` | Top message senders bar chart |
| `/least-active [days]` | Members with fewest messages (at least 1) |
| `/activity [days]` | Message activity heatmap by day and hour |
| `/vc-leaderboard [days]` | Most time spent in voice channels |
| `/top-emojis [days]` | Most used emojis server-wide |
| `/dashboard [days]` | Full server stats dashboard |

### Lookup
| Command | Description |
|---|---|
| `/word <term> [days]` | Who uses a word or phrase the most |
| `/emoji <emoji> [days]` | Who uses a specific emoji the most |
| `/top-stickers [days]` | Most used stickers server-wide |
| `/top-channels [days]` | Most active channels in the server |
| `/social-graph [days]` | Network graph of who interacts with who |

### ML Insights
| Command | Description |
|---|---|
| `/predict-active` | Predict which members will be active today |
| `/user-archetypes` | Cluster members by behavior (Power User, Lurker, etc.) |
| `/activity-spikes` | Detect unusually high activity periods |
| `/emoji-trends` | See which emojis are rising or falling in usage |

### Configuration *(Manage Server required)*
| Command | Description |
|---|---|
| `/track-word <word>` | Add a word to the tracking list |
| `/untrack-word <word>` | Remove a word from the tracking list |
| `/ignore-channel <channel>` | Stop tracking a channel |

---

## Setup

### Requirements
- Python 3.10+
- PostgreSQL

### Installation

```bash
git clone https://github.com/caicedogamer/CounterDiscord.git
cd CounterDiscord
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### Configuration

Create a `bot/config.py` file:

```python
DISCORD_TOKEN = "your_token_here"
DATABASE_URL = "postgresql://user:password@localhost:5432/discbot"
```

### Database

Run the following in your PostgreSQL database:

```sql
CREATE TABLE messages (
    message_id   BIGINT PRIMARY KEY,
    guild_id     BIGINT NOT NULL,
    channel_id   BIGINT NOT NULL,
    user_id      BIGINT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL,
    is_deleted   BOOLEAN DEFAULT FALSE
);

CREATE TABLE word_hits (
    id          BIGSERIAL PRIMARY KEY,
    guild_id    BIGINT NOT NULL,
    channel_id  BIGINT NOT NULL,
    user_id     BIGINT NOT NULL,
    word        TEXT NOT NULL,
    hit_at      TIMESTAMPTZ NOT NULL
);

CREATE TABLE emoji_hits (
    id          BIGSERIAL PRIMARY KEY,
    guild_id    BIGINT NOT NULL,
    channel_id  BIGINT NOT NULL,
    user_id     BIGINT NOT NULL,
    emoji_id    TEXT NOT NULL,
    emoji_name  TEXT,
    context     TEXT NOT NULL,
    hit_at      TIMESTAMPTZ NOT NULL
);

CREATE TABLE vc_sessions (
    id                BIGSERIAL PRIMARY KEY,
    guild_id          BIGINT NOT NULL,
    channel_id        BIGINT NOT NULL,
    user_id           BIGINT NOT NULL,
    joined_at         TIMESTAMPTZ NOT NULL,
    left_at           TIMESTAMPTZ NOT NULL,
    duration_seconds  INTEGER NOT NULL
);

CREATE TABLE guild_config (
    guild_id  BIGINT PRIMARY KEY,
    config    JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE ml_predictions (
    id               BIGSERIAL PRIMARY KEY,
    guild_id         BIGINT NOT NULL,
    prediction_type  TEXT NOT NULL,
    payload          JSONB NOT NULL,
    generated_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ml_guild_type ON ml_predictions (guild_id, prediction_type);

CREATE TABLE sticker_hits (
    id           BIGSERIAL PRIMARY KEY,
    guild_id     BIGINT NOT NULL,
    channel_id   BIGINT NOT NULL,
    user_id      BIGINT NOT NULL,
    sticker_id   BIGINT NOT NULL,
    sticker_name TEXT,
    hit_at       TIMESTAMPTZ NOT NULL
);

CREATE TABLE user_interactions (
    id          BIGSERIAL PRIMARY KEY,
    guild_id    BIGINT NOT NULL,
    channel_id  BIGINT NOT NULL,
    from_user   BIGINT NOT NULL,
    to_user     BIGINT NOT NULL,
    hit_at      TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_interactions_guild ON user_interactions (guild_id);
```

### Running

```bash
python -m bot.main
```

---

## Tech Stack

| Layer | Library |
|---|---|
| Discord | discord.py 2.x |
| Database | PostgreSQL + asyncpg |
| Charts | matplotlib, seaborn |
| Graph | networkx |
| ML | scikit-learn, pandas, numpy |
| Model persistence | joblib |

---

## Project Structure

```
bot/
├── main.py
├── config.py
├── commands/
│   ├── activity.py       # /activity heatmap
│   ├── channels.py       # /top-channels
│   ├── config.py         # /track-word, /untrack-word, /ignore-channel
│   ├── dashboard.py      # /dashboard
│   ├── emojis.py         # /emoji
│   ├── ml_insights.py    # /predict-active, /user-archetypes, /activity-spikes, /emoji-trends
│   ├── social.py         # /social-graph
│   ├── stats.py          # /leaderboard, /least-active
│   ├── stickers.py       # /top-stickers
│   ├── top_emojis.py     # /top-emojis
│   ├── vc.py             # /vc-leaderboard
│   └── words.py          # /word
├── listeners/
│   ├── messages.py       # message, word, emoji, sticker, interaction tracking
│   ├── reactions.py      # reaction emoji tracking
│   └── voice.py          # VC session tracking
├── db/
│   ├── connection.py     # asyncpg pool setup
│   └── queries.py        # all database queries
├── charts/
│   ├── renderer.py       # shared theme constants and run_in_executor
│   ├── bar.py            # horizontal bar chart
│   ├── line.py           # line chart
│   ├── heatmap.py        # activity heatmap
│   ├── graph.py          # social network graph
│   └── dashboard.py      # multi-panel server dashboard
└── ml/
    ├── features.py        # feature extraction from DB
    ├── activity.py        # activity prediction (RandomForest)
    ├── anomaly.py         # spike detection (IsolationForest)
    ├── clusters.py        # behavior clustering (KMeans)
    ├── emoji_trends.py    # emoji trend analysis (LinearRegression)
    └── models/            # saved .joblib files (gitignored)
```

> **Note:** The bot only tracks interactions from the moment it starts running — there is no backfill for historical messages.
