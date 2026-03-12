"""Unified X API client using OAuth 1.0a (HMAC-SHA1).

This module provides a single `XClient` that signs every request with
OAuth 1.0a credentials, bypassing the Pay-Per-Use Project requirement
that blocks OAuth 2.0 PKCE writes.
"""

import os
import json
from pathlib import Path
from requests_oauthlib import OAuth1Session
from dotenv import load_dotenv

# Load .env from the xclaw package root
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

BASE_V2 = "https://api.x.com/2"
BASE_UPLOAD = "https://upload.twitter.com/1.1"


def _get_session() -> OAuth1Session:
    """Create an OAuth1Session from environment variables."""
    ck = os.environ.get("CONSUMER_KEY")
    cs = os.environ.get("CONSUMER_SECRET")
    at = os.environ.get("ACCESS_TOKEN")
    ats = os.environ.get("ACCESS_TOKEN_SECRET")
    if not all([ck, cs, at, ats]):
        raise ValueError(
            "OAuth 1.0a credentials not found. "
            "Set CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET in .env"
        )
    return OAuth1Session(ck, client_secret=cs, resource_owner_key=at, resource_owner_secret=ats)


class XClient:
    """Thin wrapper around OAuth1Session for X API v2."""

    def __init__(self):
        self.session = _get_session()

    # ── helpers ──────────────────────────────────────────────
    def _url(self, path: str) -> str:
        return f"{BASE_V2}{path}"

    def _raise_for_error(self, resp, action="request"):
        if resp.status_code >= 400:
            try:
                body = resp.json()
            except Exception:
                body = resp.text
            raise RuntimeError(
                f"X API {action} failed ({resp.status_code}): {json.dumps(body, ensure_ascii=False)}"
            )

    # ── posts ────────────────────────────────────────────────
    def create_tweet(self, text: str, *, reply_to: str = None, quote: str = None, media_ids: list = None) -> dict:
        payload = {"text": text}
        if reply_to:
            payload["reply"] = {"in_reply_to_tweet_id": reply_to}
        if quote:
            payload["quote_tweet_id"] = quote
        if media_ids:
            payload["media"] = {"media_ids": media_ids}
        resp = self.session.post(self._url("/tweets"), json=payload)
        self._raise_for_error(resp, "create_tweet")
        return resp.json()

    def delete_tweet(self, tweet_id: str) -> dict:
        resp = self.session.delete(self._url(f"/tweets/{tweet_id}"))
        self._raise_for_error(resp, "delete_tweet")
        return resp.json()

    # ── search ───────────────────────────────────────────────
    def search_recent(self, query: str, *, max_results: int = 10, sort_order: str = None) -> dict:
        params = {
            "query": query,
            "max_results": max_results,
            "tweet.fields": "author_id,created_at,public_metrics,conversation_id",
        }
        if sort_order:
            params["sort_order"] = sort_order
        resp = self.session.get(self._url("/tweets/search/recent"), params=params)
        self._raise_for_error(resp, "search")
        return resp.json()

    # ── engage ───────────────────────────────────────────────
    def like(self, tweet_id: str) -> dict:
        user_id = self.get_me()["data"]["id"]
        resp = self.session.post(self._url(f"/users/{user_id}/likes"), json={"tweet_id": tweet_id})
        self._raise_for_error(resp, "like")
        return resp.json()

    def unlike(self, tweet_id: str) -> dict:
        user_id = self.get_me()["data"]["id"]
        resp = self.session.delete(self._url(f"/users/{user_id}/likes/{tweet_id}"))
        self._raise_for_error(resp, "unlike")
        return resp.json()

    def repost(self, tweet_id: str) -> dict:
        user_id = self.get_me()["data"]["id"]
        resp = self.session.post(self._url(f"/users/{user_id}/retweets"), json={"tweet_id": tweet_id})
        self._raise_for_error(resp, "repost")
        return resp.json()

    def unrepost(self, tweet_id: str) -> dict:
        user_id = self.get_me()["data"]["id"]
        resp = self.session.delete(self._url(f"/users/{user_id}/retweets/{tweet_id}"))
        self._raise_for_error(resp, "unrepost")
        return resp.json()

    # ── user ─────────────────────────────────────────────────
    def get_me(self) -> dict:
        resp = self.session.get(self._url("/users/me"))
        self._raise_for_error(resp, "get_me")
        return resp.json()

    def get_user_tweets(self, user_id: str, *, max_results: int = 10) -> dict:
        params = {
            "max_results": max_results,
            "tweet.fields": "created_at,public_metrics,text",
        }
        resp = self.session.get(self._url(f"/users/{user_id}/tweets"), params=params)
        self._raise_for_error(resp, "get_user_tweets")
        return resp.json()

    # ── tweet lookup ─────────────────────────────────────────
    def get_tweet(self, tweet_id: str) -> dict:
        params = {"tweet.fields": "author_id,created_at,public_metrics,text"}
        resp = self.session.get(self._url(f"/tweets/{tweet_id}"), params=params)
        self._raise_for_error(resp, "get_tweet")
        return resp.json()

    # ── timeline ─────────────────────────────────────────────
    def get_timeline(self, *, max_results: int = 10) -> dict:
        user_id = self.get_me()["data"]["id"]
        params = {
            "max_results": max_results,
            "tweet.fields": "author_id,created_at,public_metrics,text",
        }
        resp = self.session.get(self._url(f"/users/{user_id}/timelines/reverse_chronological"), params=params)
        self._raise_for_error(resp, "get_timeline")
        return resp.json()

    def get_mentions(self, *, max_results: int = 10) -> dict:
        user_id = self.get_me()["data"]["id"]
        params = {
            "max_results": max_results,
            "tweet.fields": "author_id,created_at,public_metrics,text",
        }
        resp = self.session.get(self._url(f"/users/{user_id}/mentions"), params=params)
        self._raise_for_error(resp, "get_mentions")
        return resp.json()

    # ── DM ───────────────────────────────────────────────────
    def send_dm(self, participant_id: str, text: str) -> dict:
        payload = {
            "message": {"text": text},
            "participant_ids": [participant_id],
            "conversation_type": "dm",
        }
        resp = self.session.post(self._url("/dm_conversations"), json=payload)
        self._raise_for_error(resp, "send_dm")
        return resp.json()

    # ── media upload (v1.1 upload endpoint, OAuth 1.0a) ──────
    def upload_media(self, file_path: str) -> str:
        """Upload image/video and return media_id_string."""
        import mimetypes
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        mime, _ = mimetypes.guess_type(str(path))
        size = path.stat().st_size

        if mime and mime.startswith("video"):
            return self._chunked_upload(path, mime, size)
        else:
            return self._simple_upload(path, mime)

    def _simple_upload(self, path: Path, mime: str) -> str:
        """Simple upload for images (< 5MB)."""
        url = f"{BASE_UPLOAD}/media/upload.json"
        with open(path, "rb") as f:
            files = {"media": (path.name, f, mime or "application/octet-stream")}
            resp = self.session.post(url, files=files)
        self._raise_for_error(resp, "media_upload")
        return resp.json()["media_id_string"]

    def _chunked_upload(self, path: Path, mime: str, size: int) -> str:
        """Chunked upload for video files."""
        import time as _time
        url = f"{BASE_UPLOAD}/media/upload.json"

        # INIT
        resp = self.session.post(url, data={
            "command": "INIT",
            "total_bytes": size,
            "media_type": mime,
            "media_category": "tweet_video",
        })
        self._raise_for_error(resp, "media_upload_init")
        media_id = resp.json()["media_id_string"]

        # APPEND
        chunk_size = 4 * 1024 * 1024  # 4MB
        with open(path, "rb") as f:
            segment = 0
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                resp = self.session.post(url, data={
                    "command": "APPEND",
                    "media_id": media_id,
                    "segment_index": segment,
                }, files={"media": chunk})
                self._raise_for_error(resp, f"media_upload_append_{segment}")
                segment += 1

        # FINALIZE
        resp = self.session.post(url, data={
            "command": "FINALIZE",
            "media_id": media_id,
        })
        self._raise_for_error(resp, "media_upload_finalize")
        result = resp.json()

        # STATUS polling (video transcoding)
        if "processing_info" in result:
            while True:
                info = result.get("processing_info", {})
                state = info.get("state")
                if state == "succeeded":
                    break
                if state == "failed":
                    raise RuntimeError(f"Video processing failed: {info}")
                wait = info.get("check_after_secs", 5)
                _time.sleep(wait)
                resp = self.session.get(url, params={
                    "command": "STATUS",
                    "media_id": media_id,
                })
                self._raise_for_error(resp, "media_upload_status")
                result = resp.json()

        return media_id
