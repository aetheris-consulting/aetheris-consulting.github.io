"""Orchestrator - Parses intent and composes execution plans."""

import logging
from typing import Any, Dict, List, Optional

from aethermcp.core.protocol import ProtocolHandler
from aethermcp.core.provenance import ProvenanceEngine
from aethermcp.core.registry import ToolRegistry
from aethermcp.core.types import (
    ExecutionMode,
    OrchestrationPlan,
    OrchestrationStep,
    TaskStatus,
    UserIntent,
)

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Orchestrates execution of user intents using available tools.

    Core responsibilities:
    - Parse user intent into structured goals
    - Query registry for relevant tools
    - Generate execution plans
    - Coordinate tool execution
    - Handle failures and iteration
    """

    def __init__(
        self,
        registry: ToolRegistry,
        protocol: ProtocolHandler,
        provenance: ProvenanceEngine,
    ) -> None:
        """
        Initialize orchestrator.

        Args:
            registry: Tool registry
            protocol: Protocol handler
            provenance: Provenance engine
        """
        self.registry = registry
        self.protocol = protocol
        self.provenance = provenance

    def parse_intent(self, user_input: str, **kwargs: Any) -> UserIntent:
        """
        Parse natural language input into structured intent.

        Args:
            user_input: Raw user request
            **kwargs: Additional parameters (budget, mode, etc.)

        Returns:
            Structured user intent
        """
        logger.info(f"Parsing intent: {user_input[:100]}...")

        # Extract mode if specified
        mode = kwargs.get("mode", ExecutionMode.NARROW)
        if isinstance(mode, str):
            mode = ExecutionMode(mode)

        # Simple keyword-based parsing (in production, use LLM)
        intent = UserIntent(
            raw_input=user_input,
            primary_objective=self._extract_objective(user_input),
            domain=self._extract_domain(user_input),
            constraints=kwargs.get("constraints", []),
            success_criteria=kwargs.get("success_criteria", []),
            budget=kwargs.get("budget"),
            mode=mode,
        )

        logger.info(f"Parsed intent: objective='{intent.primary_objective}', domain='{intent.domain}'")
        return intent

    def generate_plan(self, intent: UserIntent) -> OrchestrationPlan:
        """
        Generate execution plan from intent.

        Args:
            intent: User intent

        Returns:
            Orchestration plan
        """
        logger.info(f"Generating plan for: {intent.primary_objective}")

        # Query registry for relevant tools
        relevant_servers = self.registry.list_servers(domain=intent.domain)

        if not relevant_servers:
            logger.warning(f"No servers found for domain: {intent.domain}")

        # Generate steps (simplified - in production, use AI for complex planning)
        steps: List[OrchestrationStep] = []

        # For now, create a simple plan
        # In production, this would use templates and AI reasoning
        if "design" in intent.primary_objective.lower():
            # Design workflow
            llm_servers = self.registry.get_category_servers(
                self.registry._servers.get("claude_server", type("obj", (), {"category": None})).category
            )
            if llm_servers:
                steps.append(
                    OrchestrationStep(
                        step_id="design_1",
                        description="Generate initial design",
                        server_name=llm_servers[0].name,
                        tool_name="generate",
                        parameters={"prompt": intent.primary_objective, "temperature": 0.7},
                    )
                )

        # Estimate cost and time
        estimated_cost = sum(
            self.registry.get_server(step.server_name).cost_per_call
            for step in steps
            if self.registry.get_server(step.server_name)
        )

        plan = OrchestrationPlan(
            intent=intent,
            steps=steps,
            estimated_cost=estimated_cost,
            estimated_time=len(steps) * 30.0,  # Rough estimate
            confidence=0.8,
        )

        logger.info(
            f"Generated plan with {len(steps)} steps, "
            f"estimated cost ${estimated_cost:.2f}"
        )
        return plan

    def suggest_templates(self, intent: UserIntent) -> List[str]:
        """
        Suggest applicable templates for the intent.

        Args:
            intent: User intent

        Returns:
            List of template names
        """
        suggestions = []

        # Check for keywords that map to templates
        objective_lower = intent.primary_objective.lower()

        if any(
            word in objective_lower for word in ["secure", "security", "vulnerability", "attack"]
        ):
            suggestions.append("security_validation_template")

        if any(word in objective_lower for word in ["design", "brainstorm", "ideas"]):
            suggestions.append("multi_ai_brainstorm_template")

        if intent.budget and intent.budget < 20.0:
            suggestions.append("cost_constrained_execution_template")

        if any(
            word in objective_lower
            for word in ["validate", "verify", "check", "test", "high-fidelity"]
        ):
            suggestions.append("calibrated_scoring_template")

        logger.info(f"Suggested templates: {suggestions}")
        return suggestions

    def _extract_objective(self, user_input: str) -> str:
        """
        Extract primary objective from user input.

        Args:
            user_input: Raw input

        Returns:
            Primary objective
        """
        # Simple extraction - in production, use NLP/LLM
        # Look for action verbs
        action_verbs = ["design", "create", "build", "analyze", "validate", "test", "implement"]

        for verb in action_verbs:
            if verb in user_input.lower():
                # Return from verb onwards
                idx = user_input.lower().index(verb)
                return user_input[idx:].strip()

        # Fallback: return entire input
        return user_input

    def _extract_domain(self, user_input: str) -> str:
        """
        Extract problem domain from user input.

        Args:
            user_input: Raw input

        Returns:
            Domain identifier
        """
        # Simple keyword matching - in production, use taxonomy/LLM
        domain_keywords = {
            "security": ["security", "secure", "attack", "vulnerability", "crypto"],
            "ai": ["ai", "llm", "model", "agent", "sovereign"],
            "network": ["network", "protocol", "handshake", "communication"],
            "data": ["data", "database", "storage", "query"],
            "ui": ["ui", "interface", "design", "frontend"],
        }

        user_lower = user_input.lower()
        for domain, keywords in domain_keywords.items():
            if any(kw in user_lower for kw in keywords):
                return domain

        return "general"

    def estimate_plan_cost(self, plan: OrchestrationPlan) -> float:
        """
        Estimate total cost for a plan.

        Args:
            plan: Orchestration plan

        Returns:
            Estimated cost in USD
        """
        total = 0.0
        for step in plan.steps:
            server = self.registry.get_server(step.server_name)
            if server:
                total += server.cost_per_call

        return total

    def validate_plan(self, plan: OrchestrationPlan) -> tuple[bool, Optional[str]]:
        """
        Validate that a plan is executable.

        Args:
            plan: Orchestration plan

        Returns:
            (is_valid, error_message)
        """
        # Check budget
        if plan.intent.budget:
            if plan.estimated_cost > plan.intent.budget:
                return False, f"Estimated cost ${plan.estimated_cost:.2f} exceeds budget ${plan.intent.budget:.2f}"

        # Check all servers exist
        for step in plan.steps:
            if not self.registry.get_server(step.server_name):
                return False, f"Server '{step.server_name}' not found in registry"

        # Check dependencies are valid
        step_ids = {step.step_id for step in plan.steps}
        for step in plan.steps:
            for dep_id in step.dependencies:
                if dep_id not in step_ids:
                    return False, f"Dependency '{dep_id}' not found for step '{step.step_id}'"

        return True, None
