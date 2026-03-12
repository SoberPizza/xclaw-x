"""Engagement operations via OAuth 1.0a"""

import click
import json
from xclaw.api import XClient


@click.command()
@click.argument("tweet_id")
@click.option("--json", "output_json", is_flag=True, help="Output JSON")
def like(tweet_id, output_json):
    """Like a post."""
    client = XClient()
    result = client.like(tweet_id)
    if output_json:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        click.echo(f"✅ Liked: {tweet_id}")


@click.command()
@click.argument("tweet_id")
@click.option("--json", "output_json", is_flag=True, help="Output JSON")
def unlike(tweet_id, output_json):
    """Unlike a post."""
    client = XClient()
    result = client.unlike(tweet_id)
    if output_json:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        click.echo(f"✅ Unliked: {tweet_id}")


@click.command()
@click.argument("tweet_id")
@click.option("--json", "output_json", is_flag=True, help="Output JSON")
def repost(tweet_id, output_json):
    """Repost (retweet) a post."""
    client = XClient()
    result = client.repost(tweet_id)
    if output_json:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        click.echo(f"✅ Reposted: {tweet_id}")


@click.command()
@click.argument("tweet_id")
@click.option("--json", "output_json", is_flag=True, help="Output JSON")
def unrepost(tweet_id, output_json):
    """Undo a repost."""
    client = XClient()
    result = client.unrepost(tweet_id)
    if output_json:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        click.echo(f"✅ Unreposted: {tweet_id}")
