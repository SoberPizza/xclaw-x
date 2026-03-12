"""Core scraper engine wrapping twikit for cookie-based X access."""

import os
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

COOKIE_PATH = Path.home() / ".xclaw" / "scout_cookies.json"


def _ensure_dir():
    COOKIE_PATH.parent.mkdir(parents=True, exist_ok=True)


async def _get_client():
    """Get an authenticated twikit client, reusing cookies if possible.

    Strategy:
    1. If cookies file exists → load directly (skip login entirely)
    2. If no cookies → attempt login with SCOUT credentials
    3. If login hits Cloudflare → guide user to export browser cookies
    """
    from twikit import Client

    client = Client("en-US")

    # Strategy 1: Load saved cookies (bypasses Cloudflare entirely)
    if COOKIE_PATH.exists():
        try:
            client.load_cookies(str(COOKIE_PATH))
            return client
        except Exception:
            pass  # cookies corrupted, fall through

    # Strategy 2: Try login with credentials + cookies_file param
    username = os.environ.get("SCOUT_USERNAME")
    password = os.environ.get("SCOUT_PASSWORD")
    email = os.environ.get("SCOUT_EMAIL", "")

    if not username or not password:
        raise ValueError(
            "Scout credentials not found. "
            "Set SCOUT_USERNAME and SCOUT_PASSWORD in .env"
        )

    try:
        _ensure_dir()
        await client.login(
            auth_info_1=username,
            auth_info_2=email,
            password=password,
            cookies_file=str(COOKIE_PATH),
        )
        # Save cookies for reuse
        client.save_cookies(str(COOKIE_PATH))
        return client
    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg or "Cloudflare" in error_msg:
            raise RuntimeError(
                "Cloudflare blocked the login request.\n"
                "Run 'xclaw scout export-cookies' to extract cookies from your browser,\n"
                "or manually export cookies from X.com and save to:\n"
                f"  {COOKIE_PATH}"
            ) from e
        raise


async def scout_search(query: str, *, limit: int = 20, sort: str = "Top") -> list:
    """Search tweets via twikit scraping.

    Args:
        query: Search query (supports #hashtags, @mentions, keywords)
        limit: Max number of tweets to return
        sort: "Top", "Latest", or "Media"

    Returns:
        List of raw twikit Tweet objects
    """
    client = await _get_client()

    product_map = {"top": "Top", "latest": "Latest", "media": "Media"}
    product = product_map.get(sort.lower(), "Top")

    tweets = await client.search_tweet(query, product=product, count=limit)
    return list(tweets)[:limit]


async def scout_trends() -> list:
    """Get current trending topics."""
    client = await _get_client()
    trends = await client.get_trends("trending")
    return list(trends)


async def scout_user_tweets(username: str, *, limit: int = 20) -> list:
    """Get recent tweets from a specific user."""
    client = await _get_client()
    user = await client.get_user_by_screen_name(username)
    tweets = await user.get_tweets("Tweets", count=limit)
    return list(tweets)[:limit]


def run_sync(coro):
    """Run an async coroutine synchronously (Click compatibility)."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)
