# X/Twitter Operations — Usage Examples

Scenario-based examples for AI agents using xclaw v0.2.0.

---

## Scenario 1: Rich Media Publishing

**Goal:** Post content with images and videos

```bash
# Simple image post
xclaw post "Check out our new dashboard! 📊" --media dashboard.png

# Multi-image post
xclaw post "Before → After 🔥" --media before.png --media after.png

# Video post
xclaw post "60-second demo of our AI agent 🤖" --media demo.mp4

# Upload first, then post (useful for batch workflows)
xclaw upload banner.jpg --json > media.json
MEDIA_ID=$(cat media.json | python3 -c "import sys,json; print(json.load(sys.stdin)['media_ids'][0])")
xclaw post "Launch day! 🚀" --media $MEDIA_ID
```

## Scenario 2: Thread Creation with Media

**Goal:** Build an engaging thread with mixed content

```bash
# First post in thread
xclaw post "🧵 How we built an AI agent marketplace — a thread" --media cover.png --json > p1.json
ID=$(cat p1.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',d.get('data',{}).get('id','')))")

# Continue thread
xclaw post "1/ The architecture is surprisingly simple..." --media arch.png --reply-to $ID --json > p2.json
ID2=$(cat p2.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',d.get('data',{}).get('id','')))")

xclaw post "2/ Each agent is a self-contained unit that can..." --reply-to $ID2
xclaw post "3/ The key insight: let agents find each other through a market mechanism 🏪" --reply-to $ID2
```

## Scenario 3: Hot-Post Discovery & Lead Generation

**Goal:** Find high-engagement posts in your niche and reply strategically

```bash
# Step 1: Find hot posts about AI agents
xclaw search "#AIagents OR #AI OR \"AI agent\"" \
  --sort relevancy --min-likes 50 --max-results 50 --json > hot_posts.json

# Step 2: Analyze results (AI agent would parse JSON)
cat hot_posts.json | python3 -c "
import sys, json
posts = json.load(sys.stdin)
for p in sorted(posts, key=lambda x: x.get('public_metrics',{}).get('like_count',0), reverse=True)[:10]:
    m = p.get('public_metrics', {})
    print(f\"ID: {p['id']}  ❤️{m.get('like_count',0)}  🔁{m.get('retweet_count',0)}  {p['text'][:80]}\")
"

# Step 3: Reply with value — not spam
xclaw post "Great point! We've been experimenting with agent-to-agent collaboration. \
Here's what we learned: [link]" --reply-to 1234567890

# Step 4: Quote-tweet the best ones
xclaw post "This resonates deeply with what we're building at Xyzen 👇 \
Agents don't need a master — they need a market." --quote 9876543210
```

## Scenario 4: Competitor Intelligence

**Goal:** Monitor competitor posts with engagement data

```bash
# Search competitor content with metrics
xclaw search "from:competitor1 OR from:competitor2" \
  --max-results 100 --sort recency --json > competitors.json

# Find their top-performing content
cat competitors.json | python3 -c "
import sys, json
posts = json.load(sys.stdin)
for p in sorted(posts, key=lambda x: x.get('public_metrics',{}).get('like_count',0), reverse=True)[:5]:
    m = p.get('public_metrics', {})
    print(f\"❤️{m.get('like_count',0)} 🔁{m.get('retweet_count',0)} 💬{m.get('reply_count',0)}\")
    print(f\"  {p['text'][:120]}\")
    print()
"
```

## Scenario 5: Community Management

**Goal:** Monitor and respond to mentions efficiently

```bash
# Get recent mentions
xclaw mentions --max-results 50 --json > mentions.json

# Check for unanswered questions
cat mentions.json | python3 -c "
import sys, json
for p in json.load(sys.stdin):
    if '?' in p.get('text', ''):
        print(f\"Q: {p['id']} — {p['text'][:100]}\")
"

# Reply to questions
xclaw post "@user Thanks for reaching out! Here's the answer: ..." --reply-to 1234567890

# Send private follow-up
xclaw dm "Hey! Saw your question on our post. Happy to help in detail here." --username user123
```

## Scenario 6: Automated Daily Workflow

**Goal:** A complete daily social media routine for an AI agent

```bash
#!/bin/bash
# daily_x_routine.sh — Run via cron or AI agent scheduler

set -euo pipefail

DATE=$(date +%Y-%m-%d)
OUT_DIR="$HOME/.xclaw/daily/$DATE"
mkdir -p "$OUT_DIR"

echo "=== Step 1: Check mentions ==="
xclaw mentions --max-results 30 --json > "$OUT_DIR/mentions.json"

echo "=== Step 2: Discover hot posts in niche ==="
xclaw search "#AI #agents -is:retweet lang:en" \
  --sort relevancy --min-likes 20 --max-results 50 \
  --json > "$OUT_DIR/hot_posts.json"

echo "=== Step 3: Check timeline ==="
xclaw timeline --max-results 30 --json > "$OUT_DIR/timeline.json"

echo "=== Daily data collected at $OUT_DIR ==="
echo "AI agent should now:"
echo "  1. Parse mentions → reply to questions"
echo "  2. Parse hot_posts → reply to top 3 with value-add content"
echo "  3. Parse timeline → like/repost relevant content"
```

## Parsing JSON Output

```bash
# Extract all post IDs
xclaw search "query" --json | python3 -c "
import sys, json
for p in json.load(sys.stdin):
    print(p['id'])
"

# Sort by engagement (likes)
xclaw search "query" --json | python3 -c "
import sys, json
posts = json.load(sys.stdin)
for p in sorted(posts, key=lambda x: x.get('public_metrics',{}).get('like_count',0), reverse=True):
    m = p.get('public_metrics', {})
    print(f\"{p['id']}  ❤️{m.get('like_count',0)}  {p['text'][:80]}\")
"

# Filter by language
xclaw search "query" --json | python3 -c "
import sys, json
for p in json.load(sys.stdin):
    if p.get('lang') == 'en':
        print(f\"{p['id']}: {p['text'][:100]}\")
"
```

## Error Handling Patterns

```bash
# Auto-retry with backoff
retry_post() {
  local text="$1"
  local max_retries=3
  for i in $(seq 1 $max_retries); do
    if xclaw post "$text" 2>/dev/null; then
      return 0
    fi
    echo "Retry $i/$max_retries — waiting $((i * 30))s..."
    sleep $((i * 30))
  done
  echo "Failed after $max_retries retries"
  return 1
}

retry_post "Hello world!"

# Validate before posting
if [ ${#TEXT} -gt 280 ]; then
  echo "Error: Post exceeds 280 characters (${#TEXT})"
  exit 1
fi

# Check auth status before batch operations
if ! xclaw search "test" --max-results 1 > /dev/null 2>&1; then
  echo "Error: Authentication failed. Check BEARER_TOKEN."
  exit 1
fi
```

## Best Practices for AI Agents

1. **Always use `--json`** for machine-readable output
2. **Rate limits:** Space operations ≥2s apart; batch searches ≤15/min
3. **Token management:** Tokens auto-persist and auto-refresh; use `xclaw logout` only if needed
4. **Lead gen replies should add value** — never spam; include insights, not just links
5. **Use `--sort relevancy --min-likes N`** to find high-signal posts worth engaging with
6. **Media workflow:** For complex posts, upload first (`xclaw upload`), then post with `--media ID`
7. **Thread building:** Always capture the post ID from `--json` output for `--reply-to` chaining
