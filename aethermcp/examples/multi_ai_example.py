#!/usr/bin/env python3
"""
Multi-AI Brainstorming Example

Demonstrates using multiple LLMs for diverse idea generation.
"""

import logging

from aethermcp import AetherMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    """Run multi-AI brainstorming example."""
    logger.info("=== Multi-AI Brainstorming Example ===")

    # Initialize
    aether = AetherMCP()

    # Check available LLM servers
    llm_servers = aether.registry.list_servers(category=aether.registry._servers.get(
        "claude_server", type("obj", (), {"category": None})
    ).category if "claude_server" in aether.registry._servers else None)

    logger.info(f"\nAvailable LLM servers: {len(llm_servers)}")
    for server in llm_servers:
        logger.info(f"  - {server.name}: {', '.join(server.strengths)}")

    # Execute with multi-AI template suggestion
    logger.info("\n--- Executing Multi-AI Intent ---")
    result = aether.execute(
        intent="""
        Design a novel sovereign AI handshake protocol that ensures:
        1. Mutual authentication between AI agents
        2. Cryptographic proof of identity
        3. Resistance to replay attacks
        4. Privacy preservation
        5. Scalability to millions of agents

        Generate multiple diverse approaches.
        """,
        budget=50.0,
        mode="freefield",  # Exploratory mode for diversity
    )

    # Display results
    logger.info("\n--- Results ---")
    logger.info(f"Status: {result.status}")
    logger.info(f"Cost: ${result.cost:.2f} / ${result.intent.budget:.2f}")
    logger.info(f"Time: {result.time_elapsed:.1f}s")
    logger.info(f"Confidence: {result.confidence:.2f}")

    if result.error:
        logger.error(f"Error: {result.error}")
    else:
        logger.info(f"\nDeliverables:")
        for key, value in result.deliverables.items():
            logger.info(f"\n{key}:")
            logger.info(f"{str(value)[:200]}...")

    # Analyze provenance
    logger.info("\n--- Provenance Analysis ---")
    chain = result.provenance
    logger.info(f"Total operations: {len(chain.nodes)}")

    # Count by type
    type_counts = {}
    for node in chain.nodes:
        type_counts[node.node_type] = type_counts.get(node.node_type, 0) + 1

    logger.info("Operations by type:")
    for node_type, count in type_counts.items():
        logger.info(f"  {node_type}: {count}")


if __name__ == "__main__":
    main()
