"""Authentication utilities for X API v2 — with token persistence and auto-refresh"""

import os
import json
import time
import hashlib
from pathlib import Path
from xdk import Client
from xdk.oauth2_auth import OAuth2PKCEAuth

# Token 持久化路径
TOKEN_DIR = Path.home() / ".xclaw"
TOKEN_FILE = TOKEN_DIR / "tokens.json"


def _ensure_token_dir():
    TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.touch(exist_ok=True)


def _load_tokens():
    """从磁盘加载已缓存的 tokens"""
    _ensure_token_dir()
    try:
        content = TOKEN_FILE.read_text().strip()
        if content:
            return json.loads(content)
    except (json.JSONDecodeError, IOError):
        pass
    return {}


def _save_tokens(tokens_data):
    """将 tokens 持久化到磁盘"""
    _ensure_token_dir()
    TOKEN_FILE.write_text(json.dumps(tokens_data, indent=2))
    # 仅限当前用户可读写
    TOKEN_FILE.chmod(0o600)


def _make_scope_key(scopes):
    """根据 scopes 生成缓存 key（同一组 scopes 共享同一个 token）"""
    normalized = " ".join(sorted(scopes))
    return hashlib.sha256(normalized.encode()).hexdigest()[:12]


def _try_refresh(auth, stored):
    """尝试用 refresh_token 刷新 access_token"""
    refresh_token = stored.get("refresh_token")
    if not refresh_token:
        return None
    try:
        new_tokens = auth.refresh_token(refresh_token)
        return new_tokens
    except Exception:
        return None


def get_oauth_client(scopes):
    """
    获取 OAuth 2.0 认证客户端。
    优先使用持久化的 token → 过期则自动刷新 → 都不行才走浏览器授权。
    """
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    redirect_uri = os.environ.get("REDIRECT_URI", "https://example.com")

    if not client_id or not client_secret:
        raise ValueError("CLIENT_ID and CLIENT_SECRET environment variables required")

    auth = OAuth2PKCEAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scopes,
    )

    all_tokens = _load_tokens()
    scope_key = _make_scope_key(scopes)
    stored = all_tokens.get(scope_key)

    # 1) 尝试使用缓存的 token
    if stored:
        expires_at = stored.get("expires_at", 0)
        # 预留 60s 缓冲
        if time.time() < expires_at - 60:
            return Client(access_token=stored["access_token"])

        # 2) 尝试自动刷新
        new_tokens = _try_refresh(auth, stored)
        if new_tokens:
            new_tokens["expires_at"] = time.time() + new_tokens.get("expires_in", 7200)
            all_tokens[scope_key] = new_tokens
            _save_tokens(all_tokens)
            return Client(access_token=new_tokens["access_token"])

    # 3) 全新授权流程（仅首次或 refresh 失败时）
    auth_url = auth.get_authorization_url()
    print(f"Visit this URL to authorize:\n{auth_url}\n")
    callback_url = input("Paste the full callback URL: ")
    tokens = auth.fetch_token(authorization_response=callback_url)
    tokens["expires_at"] = time.time() + tokens.get("expires_in", 7200)

    all_tokens[scope_key] = tokens
    _save_tokens(all_tokens)

    return Client(access_token=tokens["access_token"])


def get_oauth_access_token(scopes):
    """
    与 get_oauth_client 逻辑相同，但只返回 access_token 字符串。
    用于需要直接构造 HTTP 请求头的场景（如视频上传）。
    """
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    redirect_uri = os.environ.get("REDIRECT_URI", "https://example.com")

    if not client_id or not client_secret:
        raise ValueError("CLIENT_ID and CLIENT_SECRET environment variables required")

    auth = OAuth2PKCEAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scopes,
    )

    all_tokens = _load_tokens()
    scope_key = _make_scope_key(scopes)
    stored = all_tokens.get(scope_key)

    if stored:
        expires_at = stored.get("expires_at", 0)
        if time.time() < expires_at - 60:
            return stored["access_token"]

        new_tokens = _try_refresh(auth, stored)
        if new_tokens:
            new_tokens["expires_at"] = time.time() + new_tokens.get("expires_in", 7200)
            all_tokens[scope_key] = new_tokens
            _save_tokens(all_tokens)
            return new_tokens["access_token"]

    auth_url = auth.get_authorization_url()
    print(f"Visit this URL to authorize:\n{auth_url}\n")
    callback_url = input("Paste the full callback URL: ")
    tokens = auth.fetch_token(authorization_response=callback_url)
    tokens["expires_at"] = time.time() + tokens.get("expires_in", 7200)

    all_tokens[scope_key] = tokens
    _save_tokens(all_tokens)

    return tokens["access_token"]


def get_bearer_client():
    """获取 Bearer Token 认证客户端（只读操作）"""
    bearer_token = os.environ.get("BEARER_TOKEN")
    if not bearer_token:
        raise ValueError("BEARER_TOKEN environment variable required")
    return Client(bearer_token=bearer_token)


def get_user_id(client):
    """获取当前认证用户的 ID"""
    user = client.users.me()
    return user.data.id


def clear_tokens():
    """清除所有缓存的 tokens"""
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
    print("All cached tokens cleared.")
