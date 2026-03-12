"""Parse twikit Tweet objects into standardized xclaw format."""

from datetime import datetime


def parse_tweet(tweet) -> dict:
    """Convert a twikit Tweet object to standardized dict.

    Output format is designed to be directly consumable by
    xclaw post --reply-to / xclaw engage commands.
    """
    # Extract user info
    user = tweet.user
    author = {
        "id": str(user.id) if user else None,
        "username": user.screen_name if user else None,
        "name": user.name if user else None,
        "followers_count": user.followers_count if user else 0,
        "verified": getattr(user, "verified", False),
    }

    # Extract metrics
    metrics = {
        "likes": tweet.favorite_count or 0,
        "retweets": tweet.retweet_count or 0,
        "replies": getattr(tweet, "reply_count", 0) or 0,
        "views": _safe_int(getattr(tweet, "view_count", 0)),
    }

    # Extract hashtags
    hashtags = []
    if hasattr(tweet, "hashtags") and tweet.hashtags:
        hashtags = [f"#{h}" for h in tweet.hashtags]

    # Build URL
    url = f"https://x.com/{author['username']}/status/{tweet.id}" if author["username"] else None

    # Engagement score: simple weighted metric
    engagement_score = _calc_engagement(metrics, author.get("followers_count", 0))

    return {
        "tweet_id": str(tweet.id),
        "text": tweet.full_text or tweet.text or "",
        "author": author,
        "metrics": metrics,
        "hashtags": hashtags,
        "created_at": tweet.created_at if hasattr(tweet, "created_at") else None,
        "url": url,
        "engagement_score": engagement_score,
        "lang": getattr(tweet, "lang", None),
        "is_retweet": bool(getattr(tweet, "retweeted_tweet", None)),
        "is_reply": bool(getattr(tweet, "in_reply_to", None)),
    }


def parse_tweets(tweets: list) -> list:
    """Parse a list of twikit Tweet objects."""
    return [parse_tweet(t) for t in tweets]


def filter_tweets(
    parsed: list,
    *,
    min_likes: int = 0,
    min_retweets: int = 0,
    min_followers: int = 0,
    max_age_hours: float = None,
    exclude_retweets: bool = True,
    exclude_replies: bool = False,
) -> list:
    """Filter parsed tweets by engagement and metadata criteria."""
    results = []
    for t in parsed:
        m = t["metrics"]
        a = t["author"]

        if m["likes"] < min_likes:
            continue
        if m["retweets"] < min_retweets:
            continue
        if a.get("followers_count", 0) < min_followers:
            continue
        if exclude_retweets and t.get("is_retweet"):
            continue
        if exclude_replies and t.get("is_reply"):
            continue
        if max_age_hours and t.get("created_at"):
            try:
                created = _parse_time(t["created_at"])
                if created:
                    age_h = (datetime.utcnow() - created).total_seconds() / 3600
                    if age_h > max_age_hours:
                        continue
            except Exception:
                pass

        results.append(t)

    # Sort by engagement score descending
    results.sort(key=lambda x: x.get("engagement_score", 0), reverse=True)
    return results


def format_scout_output(parsed: list, query: str) -> dict:
    """Wrap parsed tweets in the standard scout output envelope."""
    return {
        "scout_results": {
            "query": query,
            "scraped_at": datetime.utcnow().isoformat() + "Z",
            "count": len(parsed),
            "data": parsed,
        }
    }


def _calc_engagement(metrics: dict, followers: int) -> float:
    """Calculate a 0-10 engagement score."""
    total = metrics["likes"] + metrics["retweets"] * 2 + metrics["replies"] * 3
    if followers > 0:
        rate = total / followers
        # Normalize: 0.01 rate → ~5, 0.1 rate → ~10
        score = min(10.0, rate * 500)
    else:
        # Fallback: raw engagement
        score = min(10.0, total / 100)
    return round(score, 1)


def _safe_int(val) -> int:
    """Safely convert to int."""
    if val is None:
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def _parse_time(time_str) -> datetime:
    """Try to parse various time formats from twikit."""
    if isinstance(time_str, datetime):
        return time_str
    if not isinstance(time_str, str):
        return None
    # twikit typically uses: "Thu Mar 12 14:00:00 +0000 2026"
    for fmt in [
        "%a %b %d %H:%M:%S %z %Y",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
    ]:
        try:
            return datetime.strptime(time_str, fmt).replace(tzinfo=None)
        except ValueError:
            continue
    return None
