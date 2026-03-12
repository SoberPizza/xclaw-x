"""Search posts via OAuth 1.0a"""

import click
import json
from xclaw.api import XClient


@click.command()
@click.argument("query")
@click.option("--max-results", default=10, help="Number of results (10-100)")
@click.option("--sort", "sort_order", type=click.Choice(["relevancy", "recency"]), help="Sort order")
@click.option("--min-likes", default=0, type=int, help="Filter: minimum likes")
@click.option("--min-retweets", default=0, type=int, help="Filter: minimum retweets")
@click.option("--json", "output_json", is_flag=True, help="Output JSON")
def search(query, max_results, sort_order, min_likes, min_retweets, output_json):
    """Search recent posts.

    \b
    Examples:
      xclaw search "#AI" --sort relevancy --min-likes 50
      xclaw search "machine learning" --max-results 20 --json
    """
    client = XClient()
    result = client.search_recent(query, max_results=max_results, sort_order=sort_order)

    tweets = result.get("data", [])

    # Client-side filtering by engagement metrics
    if min_likes > 0 or min_retweets > 0:
        filtered = []
        for t in tweets:
            metrics = t.get("public_metrics", {})
            if metrics.get("like_count", 0) >= min_likes and metrics.get("retweet_count", 0) >= min_retweets:
                filtered.append(t)
        tweets = filtered

    if output_json:
        click.echo(json.dumps({"data": tweets, "result_count": len(tweets)}, ensure_ascii=False, indent=2))
    else:
        if not tweets:
            click.echo("No results found.")
            return
        for t in tweets:
            metrics = t.get("public_metrics", {})
            click.echo(f"\n{'─'*60}")
            click.echo(f"ID: {t['id']}")
            click.echo(f"Author: {t.get('author_id', '?')}")
            click.echo(f"Time: {t.get('created_at', '?')}")
            click.echo(f"❤️  {metrics.get('like_count',0)}  🔁 {metrics.get('retweet_count',0)}  💬 {metrics.get('reply_count',0)}")
            click.echo(f"Text: {t['text'][:200]}")
            click.echo(f"🔗 https://x.com/i/status/{t['id']}")
