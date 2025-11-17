#!/usr/bin/env python3
"""
Budget-Constrained Execution Example

Demonstrates cost tracking and budget enforcement.
"""

import logging

from aethermcp import AetherMCP
from aethermcp.governance.sentinels import CostSentinel, SentinelManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    """Run budget-constrained example."""
    logger.info("=== Budget-Constrained Execution Example ===")

    # Initialize with strict budget
    aether = AetherMCP()

    # Set up cost sentinel
    sentinel_manager = SentinelManager()
    cost_sentinel = CostSentinel(budget=10.0)
    sentinel_manager.add_sentinel(cost_sentinel)

    logger.info(f"\nBudget limit: ${cost_sentinel.budget:.2f}")

    # Execute with budget constraint
    logger.info("\n--- Executing with Budget Constraint ---")
    result = aether.execute(
        intent="Design a secure handshake protocol",
        budget=10.0,
        mode="narrow",  # Conservative mode to minimize cost
    )

    # Check sentinel
    alerts = sentinel_manager.check_all(
        {"total_cost": result.cost, "domain": result.intent.domain}
    )

    # Display results
    logger.info("\n--- Results ---")
    logger.info(f"Status: {result.status}")
    logger.info(f"Cost: ${result.cost:.2f}")
    logger.info(f"Budget: ${result.intent.budget:.2f}")
    logger.info(f"Remaining: ${result.intent.budget - result.cost:.2f}")

    if alerts:
        logger.warning(f"\n⚠ {len(alerts)} Alert(s) Triggered:")
        for alert in alerts:
            logger.warning(f"  [{alert.level}] {alert.message}")
    else:
        logger.info("\n✓ Execution completed within budget")

    # Display cost breakdown from provenance
    logger.info("\n--- Cost Breakdown ---")
    chain = result.provenance
    step_costs = []

    for node in chain.nodes:
        if node.node_type == "step" and "cost" in node.data:
            step_costs.append((node.data.get("step_id", "unknown"), node.data["cost"]))

    for step_id, cost in step_costs:
        logger.info(f"  {step_id}: ${cost:.4f}")

    logger.info(f"\nTotal: ${sum(c for _, c in step_costs):.2f}")


if __name__ == "__main__":
    main()
