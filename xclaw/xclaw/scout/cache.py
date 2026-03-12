"""Local SQLite cache to track scouted tweets and avoid duplicate engagement."""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / ".xclaw" / "scout_cache.db"


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scouted_tweets (
            tweet_id    TEXT PRIMARY KEY,
            query       TEXT,
            username    TEXT,
            text_preview TEXT,
            likes       INTEGER DEFAULT 0,
            retweets    INTEGER DEFAULT 0,
            engagement_score REAL DEFAULT 0,
            scouted_at  TEXT,
            engaged     INTEGER DEFAULT 0,
            engaged_at  TEXT
        )
    """)
    conn.commit()
    return conn


def save_tweets(parsed_tweets: list, query: str):
    """Save scouted tweets to cache."""
    conn = _get_conn()
    now = datetime.utcnow().isoformat() + "Z"
    for t in parsed_tweets:
        conn.execute("""
            INSERT OR REPLACE INTO scouted_tweets
            (tweet_id, query, username, text_preview, likes, retweets, engagement_score, scouted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            t["tweet_id"],
            query,
            t["author"].get("username", ""),
            t["text"][:200],
            t["metrics"]["likes"],
            t["metrics"]["retweets"],
            t["engagement_score"],
            now,
        ))
    conn.commit()
    conn.close()


def mark_engaged(tweet_id: str):
    """Mark a tweet as engaged (liked/replied/reposted)."""
    conn = _get_conn()
    now = datetime.utcnow().isoformat() + "Z"
    conn.execute(
        "UPDATE scouted_tweets SET engaged = 1, engaged_at = ? WHERE tweet_id = ?",
        (now, tweet_id),
    )
    conn.commit()
    conn.close()


def is_engaged(tweet_id: str) -> bool:
    """Check if we already engaged with this tweet."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT engaged FROM scouted_tweets WHERE tweet_id = ?",
        (tweet_id,),
    ).fetchone()
    conn.close()
    return bool(row and row[0])


def get_unengaged(limit: int = 20) -> list:
    """Get scouted tweets we haven't engaged with yet."""
    conn = _get_conn()
    rows = conn.execute("""
        SELECT tweet_id, query, username, text_preview, likes, retweets, engagement_score, scouted_at
        FROM scouted_tweets
        WHERE engaged = 0
        ORDER BY engagement_score DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()

    return [
        {
            "tweet_id": r[0],
            "query": r[1],
            "username": r[2],
            "text_preview": r[3],
            "likes": r[4],
            "retweets": r[5],
            "engagement_score": r[6],
            "scouted_at": r[7],
        }
        for r in rows
    ]


def get_stats() -> dict:
    """Get cache statistics."""
    conn = _get_conn()
    total = conn.execute("SELECT COUNT(*) FROM scouted_tweets").fetchone()[0]
    engaged = conn.execute("SELECT COUNT(*) FROM scouted_tweets WHERE engaged = 1").fetchone()[0]
    conn.close()
    return {"total_scouted": total, "engaged": engaged, "pending": total - engaged}
