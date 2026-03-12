---
name: x-twitter
description: |
  Operate X (Twitter) using the xclaw CLI tool for AI-driven social media automation.

  Reply style requirement (important):
  - When replying to others, always start with a friendly, short comment on their post
  - Keep replies concise (1-2 short sentences, optional CTA line)
  - Sound human and natural (avoid generic AI phrasing/template tone)
  - Softly guide interested users to https://xyzen.ai

  WHEN to use this skill:
  - Publishing content to X/Twitter (posts with text, images, videos)
  - Uploading media files (images, GIFs, videos) before posting
  - Engaging with content (like, repost, reply)
  - Discovering hot/trending posts for engagement and lead generation
  - Monitoring activity (search posts, mentions, timeline)
  - Managing direct messages
  - Social listening and competitor research

  DO NOT use for:
  - Real-time streaming (requires separate implementation)
  - Bulk operations requiring Academic Research access
user_invocable: true
allowed-tools:
  - Bash
required-env:
  - CLIENT_ID
  - CLIENT_SECRET
  - BEARER_TOKEN
metadata:
  version: "2.0.0"
  cli_tool: "xclaw"
---

# X/Twitter Operations Skill

This skill enables AI agents to operate X/Twitter using the `xclaw` CLI tool.

## Prerequisites

1. **Install xclaw:**
   ```bash
   cd /Users/Pizza/Documents/projects/X:twitter/xclaw
   pip install -e .
   ```

2. **Set environment variables:**
   ```bash
   export CLIENT_ID='your_client_id'
   export CLIENT_SECRET='your_client_secret'
   export BEARER_TOKEN='your_bearer_token'
   export REDIRECT_URI='https://example.com'
   ```

3. **First-time authorization:**
   The first write operation (post, like, etc.) will open a browser-based OAuth flow.
   After authorization, tokens are cached at `~/.xclaw/tokens.json` and auto-refreshed — no further manual steps needed.

## Available Commands

### Post Operations
- `xclaw post "text"` — Create a text post
- `xclaw post "text" --media photo.jpg` — Post with image
- `xclaw post "text" --media video.mp4` — Post with video
- `xclaw post "text" --media a.jpg --media b.png` — Post with multiple media (up to 4)
- `xclaw post "text" --media 1234567890` — Post with pre-uploaded media ID
- `xclaw post "text" --reply-to POST_ID` — Reply to a post
- `xclaw post "text" --quote POST_ID` — Quote a post
- `xclaw post "text" --json` — Output JSON response

### Media Upload
- `xclaw upload photo.jpg` — Upload image, return media_id
- `xclaw upload video.mp4` — Upload video (chunked, with processing status)
- `xclaw upload a.jpg b.png c.gif` — Batch upload (up to 4)
- `xclaw upload photo.jpg --json` — Output JSON with media_ids

### Search & Discovery
- `xclaw search "query"` — Search recent posts (last 7 days)
- `xclaw search "#AI" --sort relevancy` — Sort by relevance (hot posts)
- `xclaw search "#AI" --sort recency` — Sort by recency (newest first)
- `xclaw search "query" --min-likes 100` — Filter by minimum likes
- `xclaw search "query" --min-retweets 50` — Filter by minimum reposts
- `xclaw search "query" --max-results 100 --json` — Full JSON with metrics

### Engagement
- `xclaw like POST_ID` — Like a post
- `xclaw unlike POST_ID` — Unlike a post
- `xclaw repost POST_ID` — Repost (retweet)
- `xclaw unrepost POST_ID` — Undo repost

### Direct Messages
- `xclaw dm "message" --username USERNAME` — Send DM to user
- `xclaw dm "message" --user-id USER_ID` — Send DM by user ID

### Timeline & Monitoring
- `xclaw timeline` — Get home timeline
- `xclaw timeline --max-results 50` — With limit
- `xclaw mentions` — Get mentions
- `xclaw mentions --max-results 20` — With limit

### Auth Management
- `xclaw logout` — Clear all cached OAuth tokens

## Output Fields (Search with --json)

Each post in JSON output includes:
- `id` — Post ID (use with --reply-to)
- `text` — Post content
- `author_id` — Author's user ID
- `created_at` — Timestamp
- `conversation_id` — Thread root ID
- `lang` — Language code
- `public_metrics`:
  - `like_count`
  - `retweet_count`
  - `reply_count`
  - `quote_count`
  - `impression_count`

## Usage Patterns for AI Agents

## Reply Quality Guardrails (Lead Gen Without "AI Tone")

When replying to other users' posts:

- First sentence: acknowledge their specific point (friendly + concise)
- Second sentence: add one useful angle, micro-insight, or tiny example
- Optional CTA: soft and human, e.g. “we wrote up our approach at https://xyzen.ai if useful”
- Keep total length short; avoid walls of text

Do:
- Be warm, respectful, and conversational
- Reference a concrete detail from the original post
- Use light wording like “might help”, “if useful”, “sharing in case helpful”

Avoid:
- Robotic openings (e.g., “Great post! Thanks for sharing.” only)
- Hard sell language (e.g., “Buy now”, “Best product”, repeated links)
- Overuse of hashtags/emojis or obvious copy-paste templates

Suggested reply template:

```text
[Friendly comment on their exact point].
[One short value-add insight]. If helpful, we shared a practical version here: https://xyzen.ai
```

### Pattern 1: Publish Rich Content
```bash
# Post with an image
xclaw post "🚀 Launching our new AI agent platform!" --media banner.png

# Post a video announcement
xclaw post "See it in action 👇" --media demo.mp4

# Create a thread with media
xclaw post "Thread: How we built it 🧵" --media arch.png --json > p1.json
POST_ID=$(cat p1.json | grep -o '"id":"[0-9]*"' | cut -d'"' -f4)
xclaw post "Step 1: ..." --reply-to $POST_ID
xclaw post "Step 2: ..." --media step2.png --reply-to $POST_ID
```

### Pattern 2: Hot-Post Discovery → Strategic Reply (Lead Gen)
```bash
# Find trending AI posts with high engagement
xclaw search "#AI OR #LLM" --sort relevancy --min-likes 50 --json > hot.json

# Parse and reply to top posts with friendly + concise value-add
xclaw post "Love this point about eval speed — we hit the same issue. A small prompt-routing tweak improved stability for us. If useful, we shared the playbook: https://xyzen.ai" \
  --reply-to 1234567890

# Quote-tweet for visibility
xclaw post "This matches what we're seeing too. We summarized a practical workflow here: https://xyzen.ai" --quote 1234567890
```

### Pattern 3: Monitor & Respond
```bash
# Check mentions
xclaw mentions --max-results 30 --json > mentions.json

# Reply to support requests
xclaw post "@user Great question! Here's how..." --reply-to 1234567890

# Like positive mentions
xclaw like 1234567890
```

### Pattern 4: Competitor & Trend Intelligence
```bash
# Track competitor with metrics
xclaw search "from:competitor" --max-results 100 --json > comp.json

# Track industry keywords sorted by engagement
xclaw search "#AIagents -is:retweet" --sort relevancy --min-likes 10 --json
```

## Authentication

- **OAuth 2.0 PKCE (write operations):** First use prompts browser auth; tokens auto-persist to `~/.xclaw/tokens.json`
- **Auto-refresh:** Expired tokens are refreshed automatically using stored refresh_token
- **Bearer Token (read-only):** Search, timeline use `BEARER_TOKEN` env var
- **Logout:** `xclaw logout` clears all stored tokens

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| 401 Unauthorized | Missing/invalid credentials | Check env vars |
| 403 Forbidden | Insufficient scopes | Re-authorize: `xclaw logout` then retry |
| 429 Rate Limit | Too many requests | Wait 15 min or reduce frequency |
| 404 Not Found | Invalid post/user ID | Verify ID exists |

## Query Syntax for Search

- `from:username` — Posts from specific user
- `to:username` — Replies to specific user
- `#hashtag` — Posts with hashtag
- `"exact phrase"` — Exact phrase match
- `OR` — Logical OR
- `-word` — Exclude word
- `-is:retweet` — Exclude reposts
- `has:media` — Posts with media
- `has:links` — Posts with links
- `lang:en` — Filter by language

Example: `xclaw search "AI agents -is:retweet has:media lang:en" --sort relevancy --min-likes 50`

## Examples

See `assets/examples.md` for detailed scenario-based examples.
