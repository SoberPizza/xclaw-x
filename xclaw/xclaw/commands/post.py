"""Post operations — supports text, media, reply, and quote via OAuth 1.0a"""

import click
import json
from xclaw.api import XClient


@click.command()
@click.argument("text")
@click.option("--reply-to", help="Post ID to reply to")
@click.option("--quote", help="Post ID to quote")
@click.option("--media", multiple=True, help="Media file path OR pre-uploaded media ID (up to 4)")
@click.option("--json", "output_json", is_flag=True, help="Output JSON")
def post(text, reply_to, quote, media, output_json):
    """Create a post with optional media, reply, or quote.

    \b
    Examples:
      xclaw post "Hello world!"
      xclaw post "Check this out" --media photo.jpg
      xclaw post "Thread!" --media img1.png --media img2.png
      xclaw post "Nice post!" --reply-to 1234567890
    """
    if len(media) > 4:
        raise click.ClickException("X API allows a maximum of 4 media per post.")

    client = XClient()

    # Handle media
    media_ids = None
    if media:
        media_ids = []
        for item in media:
            if item.isdigit() and len(item) > 10:
                media_ids.append(item)
            else:
                click.echo(f"Uploading {item}...")
                mid = client.upload_media(item)
                click.echo(f"Uploaded: {mid}")
                media_ids.append(mid)

    result = client.create_tweet(text, reply_to=reply_to, quote=quote, media_ids=media_ids)

    if output_json:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        tweet_id = result.get("data", {}).get("id", "unknown")
        click.echo(f"✅ Posted: {tweet_id}")
        click.echo(f"🔗 https://x.com/i/status/{tweet_id}")
