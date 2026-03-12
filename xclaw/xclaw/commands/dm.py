"""Direct message operations via OAuth 1.0a"""

import click
import json
from xclaw.api import XClient


@click.command()
@click.argument("user_id")
@click.argument("text")
@click.option("--json", "output_json", is_flag=True, help="Output JSON")
def dm(user_id, text, output_json):
    """Send a direct message.

    \b
    Examples:
      xclaw dm 1234567890 "Hello!"
    """
    client = XClient()
    result = client.send_dm(user_id, text)
    if output_json:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        click.echo(f"✅ DM sent to user {user_id}")
