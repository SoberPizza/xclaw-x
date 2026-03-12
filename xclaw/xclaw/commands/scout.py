"""Scout commands — free discovery via scraping, bypassing paid API search."""

import click
import json
from xclaw.scout.scraper import scout_search, scout_trends, scout_user_tweets, run_sync
from xclaw.scout.parser import parse_tweets, filter_tweets, format_scout_output
from xclaw.scout import cache


@click.group()
def scout():
    """🔍 Free post discovery (no API cost).

    \b
    Scout uses cookie-based scraping to find trending posts,
    hashtags, and engagement targets — completely free.
    All write operations still go through the official API.

    \b
    Requires SCOUT_USERNAME + SCOUT_PASSWORD in .env
    """
    pass


# ── scout search ─────────────────────────────────────────────
@scout.command()
@click.argument("query")
@click.option("--limit", default=20, help="Max results to fetch (default: 20)")
@click.option("--sort", type=click.Choice(["top", "latest", "media"]), default="top", help="Sort mode")
@click.option("--min-likes", default=0, type=int, help="Filter: minimum likes")
@click.option("--min-retweets", default=0, type=int, help="Filter: minimum retweets")
@click.option("--min-followers", default=0, type=int, help="Filter: minimum author followers")
@click.option("--max-age", default=None, type=float, help="Filter: max age in hours")
@click.option("--no-retweets", is_flag=True, help="Exclude retweets (default: on)")
@click.option("--no-replies", is_flag=True, help="Exclude replies")
@click.option("--save/--no-save", default=True, help="Save results to local cache (default: on)")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def search(query, limit, sort, min_likes, min_retweets, min_followers, max_age, no_retweets, no_replies, save, output_json):
    """Search for posts (free, no API cost).

    \b
    Examples:
      xclaw scout search "#AI agents" --min-likes 100
      xclaw scout search "startup funding" --sort latest --limit 30
      xclaw scout search "@elonmusk" --min-likes 500 --json
    """
    click.echo(f"🔍 Scouting: {query} (sort={sort}, limit={limit})...")

    try:
        raw_tweets = run_sync(scout_search(query, limit=limit, sort=sort))
    except ValueError as e:
        click.echo(f"❌ {e}")
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"❌ Scraping failed: {e}")
        raise SystemExit(1)

    if not raw_tweets:
        click.echo("No results found.")
        return

    # Parse & filter
    parsed = parse_tweets(raw_tweets)
    filtered = filter_tweets(
        parsed,
        min_likes=min_likes,
        min_retweets=min_retweets,
        min_followers=min_followers,
        max_age_hours=max_age,
        exclude_retweets=not no_retweets or True,  # default exclude
        exclude_replies=no_replies,
    )

    # Save to cache
    if save:
        cache.save_tweets(filtered, query)

    # Output
    if output_json:
        output = format_scout_output(filtered, query)
        click.echo(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        click.echo(f"\n✅ Found {len(filtered)} posts (from {len(raw_tweets)} raw results)\n")
        for i, t in enumerate(filtered, 1):
            m = t["metrics"]
            a = t["author"]
            click.echo(f"{'─'*60}")
            click.echo(f"#{i}  @{a['username']} ({a['followers_count']:,} followers)")
            click.echo(f"    ❤️  {m['likes']:,}  🔁 {m['retweets']:,}  💬 {m['replies']:,}  👁  {m['views']:,}")
            click.echo(f"    📊 Score: {t['engagement_score']}")
            click.echo(f"    {t['text'][:200]}")
            if t["hashtags"]:
                click.echo(f"    🏷  {' '.join(t['hashtags'])}")
            click.echo(f"    🔗 {t['url']}")
            click.echo(f"    💡 Reply: xclaw post \"...\" --reply-to {t['tweet_id']}")
        click.echo(f"\n{'─'*60}")
        stats = cache.get_stats()
        click.echo(f"📦 Cache: {stats['total_scouted']} scouted, {stats['engaged']} engaged, {stats['pending']} pending")


# ── scout trends ─────────────────────────────────────────────
@scout.command()
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def trends(output_json):
    """Show current trending topics (free).

    \b
    Examples:
      xclaw scout trends
      xclaw scout trends --json
    """
    click.echo("📈 Fetching trends...")

    try:
        raw_trends = run_sync(scout_trends())
    except ValueError as e:
        click.echo(f"❌ {e}")
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"❌ Failed: {e}")
        raise SystemExit(1)

    if output_json:
        # twikit trend objects → serialize
        trend_list = []
        for t in raw_trends:
            trend_list.append({
                "name": getattr(t, "name", str(t)),
                "tweet_count": getattr(t, "tweet_count", None),
            })
        click.echo(json.dumps({"trends": trend_list}, ensure_ascii=False, indent=2))
    else:
        if not raw_trends:
            click.echo("No trends found.")
            return
        click.echo(f"\n🔥 Trending now ({len(raw_trends)} topics):\n")
        for i, t in enumerate(raw_trends, 1):
            name = getattr(t, "name", str(t))
            count = getattr(t, "tweet_count", None)
            count_str = f"  ({count:,} tweets)" if count else ""
            click.echo(f"  {i:>2}. {name}{count_str}")
            if i <= 5:
                click.echo(f"      💡 xclaw scout search \"{name}\" --min-likes 50")


# ── scout user ───────────────────────────────────────────────
@scout.command()
@click.argument("username")
@click.option("--limit", default=20, help="Max tweets to fetch")
@click.option("--min-likes", default=0, type=int, help="Filter: minimum likes")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def user(username, limit, min_likes, output_json):
    """Get recent tweets from a user (free, competitor research).

    \b
    Examples:
      xclaw scout user elonmusk --limit 10
      xclaw scout user openai --min-likes 100 --json
    """
    # Strip @ prefix if present
    username = username.lstrip("@")
    click.echo(f"🔍 Scouting @{username}...")

    try:
        raw_tweets = run_sync(scout_user_tweets(username, limit=limit))
    except Exception as e:
        click.echo(f"❌ Failed: {e}")
        raise SystemExit(1)

    if not raw_tweets:
        click.echo(f"No tweets found for @{username}.")
        return

    parsed = parse_tweets(raw_tweets)
    if min_likes > 0:
        parsed = [t for t in parsed if t["metrics"]["likes"] >= min_likes]

    if output_json:
        output = format_scout_output(parsed, f"@{username}")
        click.echo(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        click.echo(f"\n✅ {len(parsed)} tweets from @{username}\n")
        for i, t in enumerate(parsed, 1):
            m = t["metrics"]
            click.echo(f"{'─'*60}")
            click.echo(f"#{i}  {t.get('created_at', '?')}")
            click.echo(f"    ❤️  {m['likes']:,}  🔁 {m['retweets']:,}  💬 {m['replies']:,}  👁  {m['views']:,}")
            click.echo(f"    {t['text'][:200]}")
            click.echo(f"    🔗 {t['url']}")


# ── scout targets ────────────────────────────────────────────
@scout.command()
@click.argument("query")
@click.option("--limit", default=10, help="Max targets to return")
@click.option("--min-likes", default=50, type=int, help="Minimum likes (default: 50)")
@click.option("--min-followers", default=1000, type=int, help="Minimum author followers (default: 1000)")
@click.option("--max-age", default=24.0, type=float, help="Max age in hours (default: 24)")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON (pipe to engage)")
def targets(query, limit, min_likes, min_followers, max_age, output_json):
    """Find high-value reply targets (free, for lead gen).

    \b
    Combines search + aggressive filtering to find posts
    worth replying to. Output is ready for xclaw post --reply-to.

    \b
    Examples:
      xclaw scout targets "#AI startup" --min-likes 100
      xclaw scout targets "AI agents" --json | jq '.scout_results.data[].tweet_id'
    """
    click.echo(f"🎯 Finding reply targets: {query}...")

    try:
        raw_tweets = run_sync(scout_search(query, limit=limit * 3, sort="top"))
    except ValueError as e:
        click.echo(f"❌ {e}")
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"❌ Scraping failed: {e}")
        raise SystemExit(1)

    parsed = parse_tweets(raw_tweets)
    filtered = filter_tweets(
        parsed,
        min_likes=min_likes,
        min_followers=min_followers,
        max_age_hours=max_age,
        exclude_retweets=True,
        exclude_replies=True,
    )

    # Exclude already-engaged tweets
    filtered = [t for t in filtered if not cache.is_engaged(t["tweet_id"])]
    filtered = filtered[:limit]

    # Save to cache
    cache.save_tweets(filtered, query)

    if output_json:
        output = format_scout_output(filtered, query)
        click.echo(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        if not filtered:
            click.echo("No targets found matching criteria. Try lowering --min-likes or --min-followers.")
            return
        click.echo(f"\n🎯 {len(filtered)} reply targets:\n")
        for i, t in enumerate(filtered, 1):
            m = t["metrics"]
            a = t["author"]
            click.echo(f"{'─'*60}")
            click.echo(f"#{i}  @{a['username']} ({a['followers_count']:,} followers) — Score: {t['engagement_score']}")
            click.echo(f"    ❤️  {m['likes']:,}  🔁 {m['retweets']:,}  💬 {m['replies']:,}")
            click.echo(f"    {t['text'][:280]}")
            click.echo(f"    🔗 {t['url']}")
            click.echo(f"    ▶  xclaw post \"your reply here\" --reply-to {t['tweet_id']}")


# ── scout cache ──────────────────────────────────────────────
@scout.command()
@click.option("--pending", is_flag=True, help="Show only un-engaged tweets")
@click.option("--limit", default=20, help="Max results")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def cached(pending, limit, output_json):
    """View cached scouted tweets.

    \b
    Examples:
      xclaw scout cached --pending --limit 10
      xclaw scout cached --json
    """
    if pending:
        items = cache.get_unengaged(limit)
    else:
        items = cache.get_unengaged(limit)  # for now, same

    stats = cache.get_stats()

    if output_json:
        click.echo(json.dumps({"cached": items, "stats": stats}, ensure_ascii=False, indent=2))
    else:
        click.echo(f"\n📦 Scout Cache — {stats['total_scouted']} total, {stats['engaged']} engaged, {stats['pending']} pending\n")
        for i, item in enumerate(items, 1):
            click.echo(f"  {i}. [{item['engagement_score']}] @{item['username']} — {item['text_preview'][:100]}")
            click.echo(f"     ID: {item['tweet_id']}  Scouted: {item['scouted_at']}")


# ── scout login ──────────────────────────────────────────────
@scout.command()
def login():
    """Login to scout account and save cookies.

    \b
    Reads SCOUT_USERNAME + SCOUT_PASSWORD from .env,
    performs login, saves cookies to ~/.xclaw/scout_cookies.json
    """
    from xclaw.scout.scraper import _get_client, run_sync, COOKIE_PATH

    click.echo("🔐 Logging in to scout account...")
    try:
        run_sync(_get_client())
        click.echo(f"✅ Login successful! Cookies saved to {COOKIE_PATH}")
    except ValueError as e:
        click.echo(f"❌ {e}")
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"❌ Login failed: {e}")
        raise SystemExit(1)


# ── scout export-cookies ─────────────────────────────────────
@scout.command("export-cookies")
@click.option("--browser", type=click.Choice(["chrome", "safari", "firefox", "manual"]), default="chrome", help="Browser to export from")
def export_cookies(browser):
    """Extract X.com cookies from your browser to bypass Cloudflare.

    \b
    This is needed because X.com uses Cloudflare protection that blocks
    programmatic login. Instead, we reuse your browser's authenticated session.

    \b
    Steps:
      1. Make sure you're logged into X.com in your browser (with the scout account)
      2. Run: xclaw scout export-cookies --browser chrome
      3. If auto-export fails, use --browser manual and follow the guide

    \b
    Examples:
      xclaw scout export-cookies                    # auto-extract from Chrome
      xclaw scout export-cookies --browser safari
      xclaw scout export-cookies --browser manual   # manual guide
    """
    from xclaw.scout.scraper import COOKIE_PATH, _ensure_dir

    if browser == "manual":
        click.echo("""
🍪 Manual Cookie Export Guide
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Open X.com in your browser and make sure you're logged in (scout account)
2. Open DevTools → Application → Cookies → https://x.com
3. Copy these cookie values:
   • auth_token
   • ct0
   • twid

4. Create this JSON file:
   """ + str(COOKIE_PATH) + """

   Content:
   {
     "auth_token": "paste_value_here",
     "ct0": "paste_value_here",
     "twid": "paste_value_here"
   }

5. Verify: xclaw scout status
        """)
        return

    # Auto-export using browser_cookie3 or sqlite3 direct read
    click.echo(f"🍪 Extracting cookies from {browser}...")

    try:
        cookies = _extract_browser_cookies(browser)
        if not cookies:
            click.echo("❌ No X.com cookies found. Make sure you're logged in.")
            click.echo("   Try: xclaw scout export-cookies --browser manual")
            raise SystemExit(1)

        _ensure_dir()
        import json
        with open(COOKIE_PATH, "w") as f:
            json.dump(cookies, f, indent=2)

        click.echo(f"✅ Exported {len(cookies)} cookies to {COOKIE_PATH}")
        click.echo(f"   Keys: {', '.join(cookies.keys())}")
        click.echo(f"\n🧪 Test with: xclaw scout search \"test\" --limit 1")

    except SystemExit:
        raise
    except Exception as e:
        click.echo(f"❌ Auto-export failed: {e}")
        click.echo("   Try: xclaw scout export-cookies --browser manual")
        raise SystemExit(1)


def _extract_browser_cookies(browser: str) -> dict:
    """Extract X.com cookies from browser cookie store."""
    import sqlite3
    import shutil
    import tempfile
    from pathlib import Path

    target_domain = ".x.com"
    important_keys = {"auth_token", "ct0", "twid", "guest_id", "personalization_id"}

    if browser == "chrome":
        cookie_db = Path.home() / "Library/Application Support/Google/Chrome/Default/Cookies"
    elif browser == "safari":
        cookie_db = Path.home() / "Library/Cookies/Cookies.binarycookies"
        # Safari uses a binary format, not sqlite — need different approach
        return _extract_safari_cookies()
    elif browser == "firefox":
        # Find default profile
        profiles_dir = Path.home() / "Library/Application Support/Firefox/Profiles"
        if profiles_dir.exists():
            for profile in profiles_dir.iterdir():
                if profile.is_dir() and (profile / "cookies.sqlite").exists():
                    cookie_db = profile / "cookies.sqlite"
                    break
            else:
                raise FileNotFoundError("Firefox cookies.sqlite not found")
        else:
            raise FileNotFoundError("Firefox profiles not found")
    else:
        raise ValueError(f"Unsupported browser: {browser}")

    if not cookie_db.exists():
        raise FileNotFoundError(f"Cookie database not found: {cookie_db}")

    # Copy to temp file (browser may have a lock)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    tmp.close()
    shutil.copy2(cookie_db, tmp.name)

    cookies = {}
    try:
        conn = sqlite3.connect(tmp.name)
        cursor = conn.cursor()

        if browser == "chrome":
            # Chrome on macOS encrypts cookie values with Keychain
            # We need to decrypt them
            try:
                cookies = _extract_chrome_cookies_decrypted(tmp.name, target_domain)
            except Exception:
                # Fallback: try reading unencrypted (older Chrome)
                cursor.execute(
                    "SELECT name, value FROM cookies WHERE host_key LIKE ?",
                    (f"%{target_domain}%",)
                )
                for name, value in cursor.fetchall():
                    if value:  # only non-empty (unencrypted)
                        cookies[name] = value
        elif browser == "firefox":
            cursor.execute(
                "SELECT name, value FROM moz_cookies WHERE host LIKE ?",
                (f"%{target_domain}%",)
            )
            for name, value in cursor.fetchall():
                cookies[name] = value

        conn.close()
    finally:
        import os
        os.unlink(tmp.name)

    return cookies


def _extract_chrome_cookies_decrypted(db_path: str, domain: str) -> dict:
    """Decrypt Chrome cookies on macOS using Keychain."""
    import sqlite3
    import subprocess
    import hashlib
    from base64 import b64decode

    # Get Chrome's encryption key from Keychain
    proc = subprocess.run(
        ["security", "find-generic-password", "-w", "-s", "Chrome Safe Storage"],
        capture_output=True, text=True
    )
    if proc.returncode != 0:
        raise RuntimeError("Cannot access Chrome Keychain. Grant Terminal access in System Preferences > Privacy > Full Disk Access")

    key_password = proc.stdout.strip()

    # Derive the actual key
    import struct
    key = hashlib.pbkdf2_hmac("sha1", key_password.encode("utf-8"), b"saltysalt", 1003, dklen=16)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name, encrypted_value FROM cookies WHERE host_key LIKE ?",
        (f"%{domain}%",)
    )

    cookies = {}
    for name, encrypted_value in cursor.fetchall():
        if encrypted_value[:3] == b"v10":
            # AES-CBC decryption
            try:
                from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
                from cryptography.hazmat.backends import default_backend

                iv = b" " * 16
                cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
                decryptor = cipher.decryptor()
                decrypted = decryptor.update(encrypted_value[3:]) + decryptor.finalize()
                # Remove PKCS7 padding
                padding_len = decrypted[-1]
                cookies[name] = decrypted[:-padding_len].decode("utf-8")
            except Exception:
                continue
        elif encrypted_value:
            cookies[name] = encrypted_value.decode("utf-8", errors="ignore")

    conn.close()
    return cookies


def _extract_safari_cookies() -> dict:
    """Extract cookies from Safari's binary cookie store."""
    # Safari uses BinaryCookies format — complex to parse
    # Simpler approach: use osascript/JavaScript to extract
    import subprocess

    click.echo("⚠️  Safari cookie auto-export is limited. Trying alternative method...")
    click.echo("   For best results, use Chrome or the manual method.")

    # Try using the `cookies` utility if available
    result = subprocess.run(
        ["osascript", "-e", 'tell application "Safari" to get name of current tab of window 1'],
        capture_output=True, text=True
    )
    # Safari automation is restricted; fall back to manual
    raise RuntimeError(
        "Safari auto-export not supported on macOS. "
        "Please use Chrome or the manual method: xclaw scout export-cookies --browser manual"
    )


# ── scout status ─────────────────────────────────────────────
@scout.command()
def status():
    """Check scout login status and cache stats."""
    from xclaw.scout.scraper import COOKIE_PATH

    # Cookie status
    if COOKIE_PATH.exists():
        import os
        from datetime import datetime
        mtime = os.path.getmtime(COOKIE_PATH)
        age_h = (datetime.now().timestamp() - mtime) / 3600
        click.echo(f"🍪 Cookies: {COOKIE_PATH}")
        click.echo(f"   Age: {age_h:.1f} hours")
        click.echo(f"   Status: {'⚠️  Old (>24h), consider re-login' if age_h > 24 else '✅ Fresh'}")
    else:
        click.echo("🍪 Cookies: ❌ Not found — run `xclaw scout login` first")

    # Cache stats
    stats = cache.get_stats()
    click.echo(f"\n📦 Cache: {stats['total_scouted']} scouted, {stats['engaged']} engaged, {stats['pending']} pending")

    # Env check
    import os
    has_user = bool(os.environ.get("SCOUT_USERNAME"))
    has_pass = bool(os.environ.get("SCOUT_PASSWORD"))
    click.echo(f"\n🔑 .env: SCOUT_USERNAME={'✅' if has_user else '❌'}  SCOUT_PASSWORD={'✅' if has_pass else '❌'}")
