#!/usr/bin/env python3
"""
Simple AetherMCP Example

Demonstrates basic usage of the AetherMCP kernel.
"""

import asyncio
import logging
from pathlib import Path

from aethermcp import AetherMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main() -> None:
    """Run simple example."""
    logger.info("=== AetherMCP Simple Example ===")

    # Initialize AetherMCP
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"

    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}")
        logger.info("Using default configuration")
        config_path = None

    aether = AetherMCP(config_path=str(config_path) if config_path else None)

    # Display stats
    stats = aether.get_stats()
    logger.info(f"Registry: {stats['registry']['total']} servers")
    logger.info(f"Templates: {stats['templates']['total_templates']} templates")

    # Execute a simple intent
    logger.info("\n--- Executing Intent ---")
    result = aether.execute(
        intent="Analyze the security implications of a simple password authentication system",
        budget=5.0,
        mode="narrow",
    )

    # Display results
    logger.info("\n--- Results ---")
    logger.info(f"Session ID: {result.session_id}")
    logger.info(f"Status: {result.status}")
    logger.info(f"Cost: ${result.cost:.2f}")
    logger.info(f"Time: {result.time_elapsed:.1f}s")
    logger.info(f"Confidence: {result.confidence:.2f}")

    if result.error:
        logger.error(f"Error: {result.error}")
    else:
        logger.info(f"\nDeliverables: {len(result.deliverables)} items")
        for key, value in result.deliverables.items():
            logger.info(f"  - {key}")

    # Verify provenance
    logger.info("\n--- Provenance ---")
    if aether.provenance.verify_chain(result.session_id):
        logger.info("✓ Provenance chain verified")
        chain = result.provenance
        logger.info(f"  Total nodes: {len(chain.nodes)}")
        logger.info(f"  Root hash: {chain.root_hash[:16]}...")
    else:
        logger.error("✗ Provenance verification failed")


if __name__ == "__main__":
    main()
