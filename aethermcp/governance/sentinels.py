"""Sentinels - Autonomous circuit breakers for safety and security."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from aethermcp.core.types import AlertLevel, GovernanceAlert

logger = logging.getLogger(__name__)


class Sentinel(ABC):
    """
    Base class for sentinels.

    Sentinels are autonomous circuit breakers that monitor system state
    and halt execution when safety/security thresholds are exceeded.
    """

    def __init__(self, name: str) -> None:
        """
        Initialize sentinel.

        Args:
            name: Sentinel name
        """
        self.name = name
        self.enabled = True
        self.alerts: List[GovernanceAlert] = []

    @abstractmethod
    def check(self, state: Dict[str, Any]) -> Optional[GovernanceAlert]:
        """
        Check system state.

        Args:
            state: Current system state

        Returns:
            Alert if threshold exceeded, None otherwise
        """
        pass

    def enable(self) -> None:
        """Enable sentinel."""
        self.enabled = True
        logger.info(f"Sentinel {self.name} enabled")

    def disable(self) -> None:
        """Disable sentinel (use with extreme caution)."""
        self.enabled = False
        logger.warning(f"Sentinel {self.name} disabled")


class CostSentinel(Sentinel):
    """
    Budget enforcement sentinel.

    Halts execution if cost limit exceeded.
    """

    def __init__(self, budget: float) -> None:
        """
        Initialize cost sentinel.

        Args:
            budget: Budget limit in USD
        """
        super().__init__("cost_sentinel")
        self.budget = budget
        self.spent = 0.0

    def check(self, state: Dict[str, Any]) -> Optional[GovernanceAlert]:
        """Check if budget exceeded."""
        if not self.enabled:
            return None

        current_cost = state.get("total_cost", 0.0)
        self.spent = current_cost

        if current_cost > self.budget:
            alert = GovernanceAlert(
                alert_id=f"cost_{datetime.utcnow().timestamp()}",
                level=AlertLevel.CRITICAL,
                message=f"Budget exceeded: ${current_cost:.2f} > ${self.budget:.2f}",
                source=self.name,
                requires_action=True,
                metadata={
                    "budget": self.budget,
                    "spent": current_cost,
                    "overage": current_cost - self.budget,
                },
            )
            self.alerts.append(alert)
            logger.critical(f"Budget sentinel triggered: {alert.message}")
            return alert

        return None

    def update_budget(self, new_budget: float) -> None:
        """
        Update budget limit.

        Args:
            new_budget: New budget in USD
        """
        old_budget = self.budget
        self.budget = new_budget
        logger.info(f"Budget updated: ${old_budget:.2f} -> ${new_budget:.2f}")


class SecuritySentinel(Sentinel):
    """
    Security validation sentinel.

    Halts execution on critical security failures.
    """

    def __init__(self) -> None:
        """Initialize security sentinel."""
        super().__init__("security_sentinel")
        self.violations: List[Dict[str, Any]] = []

    def check(self, state: Dict[str, Any]) -> Optional[GovernanceAlert]:
        """Check for security violations."""
        if not self.enabled:
            return None

        # Check for critical validation failures
        validation_results = state.get("validation_results", {})

        critical_failures = [
            result
            for result in validation_results.values()
            if isinstance(result, dict) and result.get("severity") == "critical"
        ]

        if critical_failures:
            alert = GovernanceAlert(
                alert_id=f"security_{datetime.utcnow().timestamp()}",
                level=AlertLevel.CRITICAL,
                message=f"Critical security validation failed: {len(critical_failures)} issues",
                source=self.name,
                requires_action=True,
                metadata={
                    "failures": critical_failures,
                    "count": len(critical_failures),
                },
            )
            self.alerts.append(alert)
            self.violations.extend(critical_failures)
            logger.critical(f"Security sentinel triggered: {alert.message}")
            return alert

        return None


class ValidationSentinel(Sentinel):
    """
    Validation quality sentinel.

    Ensures high-fidelity validation is performed for high-stakes domains.
    """

    def __init__(self, min_confidence: float = 0.80) -> None:
        """
        Initialize validation sentinel.

        Args:
            min_confidence: Minimum confidence threshold
        """
        super().__init__("validation_sentinel")
        self.min_confidence = min_confidence

    def check(self, state: Dict[str, Any]) -> Optional[GovernanceAlert]:
        """Check validation quality."""
        if not self.enabled:
            return None

        # Check if high-stakes domain
        domain = state.get("domain", "")
        high_stakes = any(
            keyword in domain.lower()
            for keyword in ["security", "safety", "health", "financial"]
        )

        if not high_stakes:
            return None

        # Check confidence level
        confidence = state.get("confidence", 0.0)

        if confidence < self.min_confidence:
            alert = GovernanceAlert(
                alert_id=f"validation_{datetime.utcnow().timestamp()}",
                level=AlertLevel.WARNING,
                message=f"Low confidence in high-stakes domain: {confidence:.2f} < {self.min_confidence:.2f}",
                source=self.name,
                requires_action=True,
                metadata={
                    "domain": domain,
                    "confidence": confidence,
                    "min_required": self.min_confidence,
                },
            )
            self.alerts.append(alert)
            logger.warning(f"Validation sentinel triggered: {alert.message}")
            return alert

        return None


class SentinelManager:
    """
    Manages all sentinels and coordinates checks.
    """

    def __init__(self) -> None:
        """Initialize sentinel manager."""
        self.sentinels: List[Sentinel] = []
        self.alerts: List[GovernanceAlert] = []

    def add_sentinel(self, sentinel: Sentinel) -> None:
        """
        Add a sentinel.

        Args:
            sentinel: Sentinel to add
        """
        self.sentinels.append(sentinel)
        logger.info(f"Added sentinel: {sentinel.name}")

    def remove_sentinel(self, name: str) -> None:
        """
        Remove a sentinel.

        Args:
            name: Sentinel name
        """
        self.sentinels = [s for s in self.sentinels if s.name != name]
        logger.info(f"Removed sentinel: {name}")

    def check_all(self, state: Dict[str, Any]) -> List[GovernanceAlert]:
        """
        Run all sentinel checks.

        Args:
            state: Current system state

        Returns:
            List of alerts (empty if all clear)
        """
        alerts = []

        for sentinel in self.sentinels:
            if sentinel.enabled:
                alert = sentinel.check(state)
                if alert:
                    alerts.append(alert)
                    self.alerts.append(alert)

        return alerts

    def has_critical_alerts(self) -> bool:
        """
        Check if any critical alerts exist.

        Returns:
            True if critical alerts present
        """
        return any(a.level == AlertLevel.CRITICAL for a in self.alerts)

    def get_active_alerts(self) -> List[GovernanceAlert]:
        """
        Get all active alerts.

        Returns:
            List of alerts
        """
        return self.alerts

    def clear_alerts(self) -> None:
        """Clear all alerts."""
        self.alerts.clear()
        for sentinel in self.sentinels:
            sentinel.alerts.clear()
        logger.info("Cleared all alerts")
