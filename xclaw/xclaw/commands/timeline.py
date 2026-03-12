"""Timeline and mentions via OAuth 1.0a"""

import click
import json
from xclaw.api import XClient


@click.command()
@click.option("--max-results", default=10, help="Number of results")
@click.option("--json", "output_json", is_flag=True, help="Output JSON")
def timeline(max_results, output_json):
    """Get reverse-chronological timeline."""
    client = XClient()
    result = client.get_timeline(max_results=max_results)
    tweets = result.get("data", [])
    if output_json:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for t in tweets:
            click.echo(f"\n{'─'*60}")
            click.echo(f"ID: {t['id']}  Author: {t.get('author_id','?')}")
            click.echo(f"Text: {t['text'][:200]}")


@click.command()
@click.option("--max-results", default=10, help="Number of results")
@click.option("--json", "output_json", is_flag=True, help="Output JSON")
def mentions(max_results, output_json):
    """Get recent mentions."""
    client = XClient()
    result = client.get_mentions(max_results=max_results)
    tweets = result.get("data", [])
    if output_json:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if not tweets:
            click.echo("No mentions found.")
            return
        for t in tweets:
            click.echo(f"\n{'─'*60}")
            click.echo(f"ID: {t['id']}  Author: {t.get('author_id','?')}")
            click.echo(f"Text: {t['text'][:200]}")
