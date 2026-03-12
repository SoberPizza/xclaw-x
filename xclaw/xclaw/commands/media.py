"""Media upload via OAuth 1.0a"""

import click
import json
from xclaw.api import XClient


@click.command()
@click.argument("file_path")
@click.option("--json", "output_json", is_flag=True, help="Output JSON")
def upload(file_path, output_json):
    """Upload media (image/video) and return media_id.

    \b
    Examples:
      xclaw upload photo.jpg
      xclaw upload video.mp4 --json
    """
    client = XClient()
    click.echo(f"Uploading {file_path}...")
    media_id = client.upload_media(file_path)
    if output_json:
        click.echo(json.dumps({"media_id": media_id}))
    else:
        click.echo(f"✅ Uploaded: {media_id}")
        click.echo(f"Use with: xclaw post \"text\" --media {media_id}")
