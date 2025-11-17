#!/usr/bin/env python3
"""
AetherMCP Command Line Interface

Usage:
    python -m aethermcp execute "your intent here"
    python -m aethermcp stats
    python -m aethermcp verify <session_id>
"""

import logging
import sys
from pathlib import Path

import click

from aethermcp import AetherMCP


@click.group()
@click.option("--config", type=click.Path(exists=True), help="Path to configuration file")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx: click.Context, config: str | None, verbose: bool) -> None:
    """AetherMCP - AI Exploration Framework Operating System."""
    # Configure logging
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Initialize AetherMCP
    ctx.obj = AetherMCP(config_path=config)


@cli.command()
@click.argument("intent")
@click.option("--budget", type=float, help="Budget limit in USD")
@click.option("--mode", type=click.Choice(["narrow", "freefield"]), default="narrow")
@click.option("--output", "-o", type=click.Path(), help="Output file for results")
@click.pass_obj
def execute(aether: AetherMCP, intent: str, budget: float | None, mode: str, output: str | None) -> None:
    """Execute a user intent."""
    click.echo(f"Executing intent: {intent[:100]}...")

    if budget:
        click.echo(f"Budget: ${budget:.2f}")

    # Execute
    result = aether.execute(intent=intent, budget=budget, mode=mode)

    # Display results
    click.echo("\n--- Results ---")
    click.echo(f"Session ID: {result.session_id}")
    click.echo(f"Status: {result.status}")
    click.echo(f"Cost: ${result.cost:.2f}")
    click.echo(f"Time: {result.time_elapsed:.1f}s")
    click.echo(f"Confidence: {result.confidence:.2f}")

    if result.error:
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)

    # Output results
    if output:
        import json

        output_path = Path(output)
        with open(output_path, "w") as f:
            json.dump(
                {
                    "session_id": result.session_id,
                    "intent": result.intent.model_dump(),
                    "deliverables": result.deliverables,
                    "cost": result.cost,
                    "time_elapsed": result.time_elapsed,
                    "confidence": result.confidence,
                },
                f,
                indent=2,
            )
        click.echo(f"\nResults written to: {output_path}")


@cli.command()
@click.pass_obj
def stats(aether: AetherMCP) -> None:
    """Display system statistics."""
    stats_data = aether.get_stats()

    click.echo("=== AetherMCP Statistics ===\n")

    click.echo("Registry:")
    click.echo(f"  Total servers: {stats_data['registry']['total']}")
    for category, count in stats_data['registry'].items():
        if category != "total":
            click.echo(f"  {category}: {count}")

    click.echo("\nTemplates:")
    click.echo(f"  Total: {stats_data['templates']['total_templates']}")
    for template_name in stats_data['templates']['templates']:
        click.echo(f"    - {template_name}")

    click.echo("\nProvenance:")
    click.echo(f"  Total sessions: {stats_data['provenance']['total_sessions']}")
    click.echo(f"  Total nodes: {stats_data['provenance']['total_nodes']}")


@cli.command()
@click.argument("session_id")
@click.pass_obj
def verify(aether: AetherMCP, session_id: str) -> None:
    """Verify provenance chain for a session."""
    click.echo(f"Verifying session: {session_id}")

    if aether.provenance.verify_chain(session_id):
        click.echo("✓ Provenance chain verified")

        chain = aether.provenance.get_chain(session_id)
        if chain:
            click.echo(f"  Total nodes: {len(chain.nodes)}")
            click.echo(f"  Root hash: {chain.root_hash}")
    else:
        click.echo("✗ Provenance verification failed", err=True)
        sys.exit(1)


@cli.command()
@click.argument("session_id")
@click.option("--output", "-o", type=click.Path(), required=True)
@click.pass_obj
def export(aether: AetherMCP, session_id: str, output: str) -> None:
    """Export provenance chain."""
    click.echo(f"Exporting session: {session_id}")

    chain_data = aether.provenance.export_chain(session_id)
    if not chain_data:
        click.echo(f"Session not found: {session_id}", err=True)
        sys.exit(1)

    import json

    output_path = Path(output)
    with open(output_path, "w") as f:
        json.dump(chain_data, f, indent=2, default=str)

    click.echo(f"Provenance chain exported to: {output_path}")


@cli.command()
def templates(  ) -> None:
    """List available templates."""
    aether = AetherMCP()
    template_list = aether.templates.list_templates()

    click.echo("=== Available Templates ===\n")
    for template in template_list:
        click.echo(f"{template.name}")
        click.echo(f"  Description: {template.description}")
        click.echo(f"  When to use: {template.when_to_use}")
        click.echo(f"  Steps: {len(template.steps)}")
        click.echo()


if __name__ == "__main__":
    cli()
