"""look command — full perception pipeline."""

import json
import logging

import click

from xclaw.cli.core import output

logger = logging.getLogger(__name__)


@click.command()
def look():
    """Observe the screen."""
    from xclaw.core.perception.engine import PerceptionEngine

    engine = PerceptionEngine.get_instance()
    result = engine.full_look()
    output(json.dumps(result, ensure_ascii=False))
