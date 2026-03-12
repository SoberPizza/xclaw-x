"""Main CLI interface for xclaw"""

import click
from xclaw.commands import post, search, engage, dm, timeline, media
from xclaw.commands.scout import scout


@click.group()
@click.version_option(version="0.4.0")
def cli():
    """xclaw — X (Twitter) CLI for AI agents and humans (OAuth 1.0a)"""
    pass


# Post & Media
cli.add_command(post.post)
cli.add_command(media.upload)

# Search & Discovery (API)
cli.add_command(search.search)

# Scout — Free Discovery (scraping)
cli.add_command(scout)

# Engagement
cli.add_command(engage.like)
cli.add_command(engage.unlike)
cli.add_command(engage.repost)
cli.add_command(engage.unrepost)

# DM
cli.add_command(dm.dm)

# Timeline
cli.add_command(timeline.timeline)
cli.add_command(timeline.mentions)


# Utility: whoami
@cli.command()
def whoami():
    """Show the authenticated user info."""
    from xclaw.api import XClient
    client = XClient()
    result = client.get_me()
    data = result.get("data", {})
    click.echo(f"ID: {data.get('id')}")
    click.echo(f"Name: {data.get('name')}")
    click.echo(f"Username: @{data.get('username')}")


if __name__ == "__main__":
    cli()
