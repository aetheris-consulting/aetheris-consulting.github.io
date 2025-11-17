"""Cognitive Guardian - Operator digital twin for behavioral anomaly detection."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from aethermcp.core.types import AlertLevel, GovernanceAlert, OperatorProfile

logger = logging.getLogger(__name__)


class CognitiveGuardian:
    """
    Operator digital twin that detects behavioral anomalies.

    Tracks operator patterns and alerts on significant deviations:
    - 2-sigma: Flag unusual pattern
    - 3-sigma: Require justification + two-person rule
    """

    def __init__(self, operator_id: str) -> None:
        """
        Initialize cognitive guardian.

        Args:
            operator_id: Operator identifier
        """
        self.operator_id = operator_id
        self.profile = OperatorProfile(operator_id=operator_id)
        self.history: List[Dict[str, Any]] = []
        self.alerts: List[GovernanceAlert] = []

    def record_decision(
        self,
        decision_type: str,
        parameters: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record an operator decision.

        Args:
            decision_type: Type of decision (e.g., "template_selection", "budget_approval")
            parameters: Decision parameters
            metadata: Optional metadata
        """
        record = {
            "timestamp": datetime.utcnow(),
            "decision_type": decision_type,
            "parameters": parameters,
            "metadata": metadata or {},
        }

        self.history.append(record)
        logger.debug(f"Recorded decision: {decision_type}")

        # Update profile
        self._update_profile(decision_type, parameters)

    def check_anomaly(
        self, decision_type: str, parameters: Dict[str, Any]
    ) -> Optional[GovernanceAlert]:
        """
        Check if a decision is anomalous.

        Args:
            decision_type: Type of decision
            parameters: Decision parameters

        Returns:
            Alert if anomaly detected, None otherwise
        """
        if len(self.history) < 10:
            # Not enough history for baseline
            return None

        # Calculate deviation from baseline
        deviation = self._calculate_deviation(decision_type, parameters)

        if deviation >= 3.0:
            # 3-sigma deviation: critical alert
            alert = GovernanceAlert(
                alert_id=f"cg_{datetime.utcnow().timestamp()}",
                level=AlertLevel.CRITICAL,
                message=f"Critical behavioral deviation detected: {deviation:.2f}σ from baseline",
                source="cognitive_guardian",
                requires_action=True,
                metadata={
                    "operator_id": self.operator_id,
                    "decision_type": decision_type,
                    "deviation": deviation,
                    "parameters": parameters,
                },
            )
            self.alerts.append(alert)
            logger.warning(f"3-sigma anomaly detected: {alert.message}")
            return alert

        elif deviation >= 2.0:
            # 2-sigma deviation: warning
            alert = GovernanceAlert(
                alert_id=f"cg_{datetime.utcnow().timestamp()}",
                level=AlertLevel.WARNING,
                message=f"Unusual behavioral pattern detected: {deviation:.2f}σ from baseline",
                source="cognitive_guardian",
                requires_action=False,
                metadata={
                    "operator_id": self.operator_id,
                    "decision_type": decision_type,
                    "deviation": deviation,
                    "parameters": parameters,
                },
            )
            self.alerts.append(alert)
            logger.info(f"2-sigma anomaly detected: {alert.message}")
            return alert

        return None

    def get_baseline_stats(self) -> Dict[str, Any]:
        """
        Get baseline statistics for operator.

        Returns:
            Statistics dictionary
        """
        if not self.history:
            return {}

        decision_types = {}
        for record in self.history:
            dt = record["decision_type"]
            decision_types[dt] = decision_types.get(dt, 0) + 1

        return {
            "total_decisions": len(self.history),
            "decision_types": decision_types,
            "risk_tolerance": self.profile.risk_tolerance,
            "baseline_deviation": self.profile.baseline_deviation,
        }

    def _update_profile(self, decision_type: str, parameters: Dict[str, Any]) -> None:
        """
        Update operator profile based on decision.

        Args:
            decision_type: Type of decision
            parameters: Decision parameters
        """
        # Update selection patterns
        if decision_type in self.profile.selection_patterns:
            self.profile.selection_patterns[decision_type] += 1
        else:
            self.profile.selection_patterns[decision_type] = 1

        # Update risk tolerance based on budget decisions
        if decision_type == "budget_approval" and "amount" in parameters:
            # Higher budgets = higher risk tolerance
            amount = parameters["amount"]
            current_tolerance = self.profile.risk_tolerance
            # Exponential moving average
            alpha = 0.1
            normalized_amount = min(amount / 1000.0, 1.0)  # Normalize to 0-1
            self.profile.risk_tolerance = (1 - alpha) * current_tolerance + alpha * normalized_amount

    def _calculate_deviation(
        self, decision_type: str, parameters: Dict[str, Any]
    ) -> float:
        """
        Calculate statistical deviation from baseline.

        Args:
            decision_type: Type of decision
            parameters: Decision parameters

        Returns:
            Deviation in standard deviations (sigma)
        """
        # Simple heuristic for demo purposes
        # In production, use proper statistical analysis

        # Count historical decisions of this type
        historical_count = sum(
            1 for r in self.history if r["decision_type"] == decision_type
        )

        if historical_count == 0:
            # New decision type: moderate deviation
            return 1.5

        # Check for unusual parameter values
        deviation = 0.0

        # Example: budget decisions
        if decision_type == "budget_approval" and "amount" in parameters:
            amount = parameters["amount"]
            historical_amounts = [
                r["parameters"].get("amount", 0)
                for r in self.history
                if r["decision_type"] == "budget_approval"
            ]

            if historical_amounts:
                import statistics

                mean = statistics.mean(historical_amounts)
                stdev = statistics.stdev(historical_amounts) if len(historical_amounts) > 1 else mean * 0.1

                if stdev > 0:
                    deviation = abs(amount - mean) / stdev

        return deviation

    def reset_baseline(self) -> None:
        """Reset operator baseline (use with caution)."""
        self.history.clear()
        self.profile.selection_patterns.clear()
        self.profile.risk_tolerance = 0.5
        self.profile.baseline_deviation = 0.0
        logger.warning(f"Reset baseline for operator {self.operator_id}")
