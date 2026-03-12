# xclaw - X (Twitter) API v2 CLI Tool

Command-line tool for X (Twitter) API v2 operations.

## Installation

```bash
cd xclaw
pip install -e .
```

## Setup

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Add your X API credentials:
```bash
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
BEARER_TOKEN=your_bearer_token
REDIRECT_URI=https://example.com
```

3. Export environment variables:
```bash
export $(cat .env | xargs)
```

## Commands

### Post Operations
```bash
xclaw post "Hello world!"
xclaw post "Reply text" --reply-to POST_ID
xclaw post "Quote text" --quote POST_ID
```

### Search
```bash
xclaw search "from:XDevelopers" --max-results 50
xclaw search "#AI" --json
```

### Engagement
```bash
xclaw like POST_ID
xclaw unlike POST_ID
xclaw repost POST_ID
xclaw unrepost POST_ID
```

### Direct Messages
```bash
xclaw dm "Hello!" --username target_user
xclaw dm "Hello!" --user-id USER_ID
```

### Timeline
```bash
xclaw timeline --max-results 20
xclaw mentions --max-results 10
```

## Authentication

- **OAuth 2.0 (write operations):** First use prompts for authorization
- **Bearer Token (read-only):** Used for search operations

## Output

Add `--json` flag for machine-readable JSON output:
```bash
xclaw search "query" --json > results.json
```
