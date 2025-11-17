"""AetherMCP Kernel - Main orchestration engine."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import yaml
from aethermcp.core.orchestrator import Orchestrator
from aethermcp.core.protocol import ProtocolHandler
from aethermcp.core.provenance import ProvenanceEngine
from aethermcp.core.registry import ToolRegistry
from aethermcp.core.types import (
    ExecutionResult,
    MCPResponse,
    OrchestrationPlan,
    TaskStatus,
    UserIntent,
)
from aethermcp.templates.library import TemplateLibrary

logger = logging.getLogger(__name__)


class AetherMCP:
    """
    Main AetherMCP kernel.

    Provides the primary interface for:
    - Executing user intents
    - Managing MCP servers
    - Tracking provenance
    - Enforcing governance
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        registry: Optional[ToolRegistry] = None,
        provenance: Optional[ProvenanceEngine] = None,
    ) -> None:
        """
        Initialize AetherMCP kernel.

        Args:
            config_path: Path to configuration file
            registry: Optional pre-configured registry
            provenance: Optional pre-configured provenance engine
        """
        self.config = self._load_config(config_path) if config_path else {}

        # Initialize components
        self.registry = registry or ToolRegistry()
        self.provenance = provenance or ProvenanceEngine()
        self.protocol = ProtocolHandler(
            timeout=self.config.get("timeout", 60.0),
            max_retries=self.config.get("max_retries", 3),
        )
        self.orchestrator = Orchestrator(
            registry=self.registry, protocol=self.protocol, provenance=self.provenance
        )
        self.templates = TemplateLibrary()

        # Load servers from config
        if "servers" in self.config:
            self._load_servers(self.config["servers"])

        # Load templates from config
        if "templates" in self.config:
            self._load_templates(self.config["templates"])

        logger.info("AetherMCP kernel initialized")

    def execute(
        self,
        intent: str,
        budget: Optional[float] = None,
        constraints: Optional[List[str]] = None,
        mode: str = "narrow",
        **kwargs: Any,
    ) -> ExecutionResult:
        """
        Execute a user intent (synchronous wrapper).

        Args:
            intent: Natural language description of goal
            budget: Optional cost limit in USD
            constraints: Optional list of constraints
            mode: Execution mode ("narrow" or "freefield")
            **kwargs: Additional parameters

        Returns:
            Execution result
        """
        return asyncio.run(
            self.execute_async(
                intent=intent,
                budget=budget,
                constraints=constraints,
                mode=mode,
                **kwargs,
            )
        )

    async def execute_async(
        self,
        intent: str,
        budget: Optional[float] = None,
        constraints: Optional[List[str]] = None,
        mode: str = "narrow",
        **kwargs: Any,
    ) -> ExecutionResult:
        """
        Execute a user intent (asynchronous).

        This is the main entry point for intent execution.

        Args:
            intent: Natural language description of goal
            budget: Optional cost limit in USD
            constraints: Optional list of constraints
            mode: Execution mode ("narrow" or "freefield")
            **kwargs: Additional parameters

        Returns:
            Execution result
        """
        session_id = self.provenance.create_session()
        start_time = asyncio.get_event_loop().time()

        try:
            logger.info(f"Session {session_id}: Executing intent")

            # Step 1: Parse intent
            parsed_intent = self.orchestrator.parse_intent(
                intent, budget=budget, constraints=constraints or [], mode=mode, **kwargs
            )

            intent_node_id = self.provenance.record_intent(
                session_id, parsed_intent.model_dump()
            )

            # Step 2: Generate plan
            plan = self.orchestrator.generate_plan(parsed_intent)

            # Validate plan
            is_valid, error = self.orchestrator.validate_plan(plan)
            if not is_valid:
                logger.error(f"Session {session_id}: Plan validation failed: {error}")
                return ExecutionResult(
                    session_id=session_id,
                    intent=parsed_intent,
                    provenance=self.provenance.get_chain(session_id),
                    status=TaskStatus.FAILED,
                    error=error,
                )

            plan_node_id = self.provenance.record_plan(
                session_id, plan.model_dump(), parent_id=intent_node_id
            )

            # Step 3: Execute plan
            async with self.protocol:
                deliverables, total_cost = await self._execute_plan(
                    session_id, plan, plan_node_id
                )

            # Step 4: Build result
            end_time = asyncio.get_event_loop().time()
            elapsed = end_time - start_time

            result = ExecutionResult(
                session_id=session_id,
                intent=parsed_intent,
                deliverables=deliverables,
                provenance=self.provenance.get_chain(session_id),
                cost=total_cost,
                time_elapsed=elapsed,
                confidence=plan.confidence,
                status=TaskStatus.COMPLETED,
            )

            logger.info(
                f"Session {session_id}: Completed in {elapsed:.1f}s, "
                f"cost ${total_cost:.2f}"
            )

            return result

        except Exception as e:
            logger.error(f"Session {session_id}: Execution failed: {e}", exc_info=True)

            end_time = asyncio.get_event_loop().time()
            elapsed = end_time - start_time

            return ExecutionResult(
                session_id=session_id,
                intent=parsed_intent if "parsed_intent" in locals() else UserIntent(
                    raw_input=intent,
                    primary_objective=intent,
                    domain="unknown",
                ),
                provenance=self.provenance.get_chain(session_id),
                cost=self.provenance.compute_session_cost(session_id),
                time_elapsed=elapsed,
                status=TaskStatus.FAILED,
                error=str(e),
            )

    async def _execute_plan(
        self, session_id: str, plan: OrchestrationPlan, plan_node_id: str
    ) -> tuple[Dict[str, Any], float]:
        """
        Execute an orchestration plan.

        Args:
            session_id: Session ID
            plan: Orchestration plan
            plan_node_id: Provenance node ID for plan

        Returns:
            (deliverables, total_cost)
        """
        deliverables: Dict[str, Any] = {}
        total_cost = 0.0

        # Group steps by parallel_group
        sequential_groups: List[List[Any]] = []
        current_group: List[Any] = []
        current_parallel_id = None

        for step in plan.steps:
            if step.parallel_group != current_parallel_id:
                if current_group:
                    sequential_groups.append(current_group)
                current_group = [step]
                current_parallel_id = step.parallel_group
            else:
                current_group.append(step)

        if current_group:
            sequential_groups.append(current_group)

        # Execute groups sequentially, steps within group in parallel
        for group in sequential_groups:
            tasks = []
            for step in group:
                tasks.append(self._execute_step(session_id, step, plan_node_id))

            # Run parallel steps
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for step, result in zip(group, results):
                if isinstance(result, Exception):
                    logger.error(f"Step {step.step_id} failed: {result}")
                    step.status = TaskStatus.FAILED
                else:
                    response, cost = result
                    total_cost += cost
                    deliverables[step.step_id] = response.result
                    step.status = TaskStatus.COMPLETED

        return deliverables, total_cost

    async def _execute_step(
        self, session_id: str, step: Any, parent_node_id: str
    ) -> tuple[MCPResponse, float]:
        """
        Execute a single orchestration step.

        Args:
            session_id: Session ID
            step: Orchestration step
            parent_node_id: Parent provenance node ID

        Returns:
            (response, cost)
        """
        logger.info(f"Executing step: {step.step_id} - {step.description}")

        # Get server spec
        server = self.registry.get_server(step.server_name)
        if not server:
            raise ValueError(f"Server '{step.server_name}' not found")

        # Record step start
        step_node_id = self.provenance.record_step(
            session_id,
            {
                "step_id": step.step_id,
                "server": step.server_name,
                "tool": step.tool_name,
                "parameters": step.parameters,
            },
            parent_id=parent_node_id,
        )

        # Execute request
        response = await self.protocol.send_request(
            server, step.tool_name, step.parameters
        )

        # Record result
        self.provenance.record_result(
            session_id,
            {
                "step_id": step.step_id,
                "result": response.result,
                "cost": response.cost,
                "error": response.error,
            },
            parent_id=step_node_id,
        )

        return response, response.cost

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to config file

        Returns:
            Configuration dictionary
        """
        path = Path(config_path)
        if not path.exists():
            logger.warning(f"Config file not found: {config_path}")
            return {}

        with open(path) as f:
            config = yaml.safe_load(f)

        logger.info(f"Loaded configuration from {config_path}")
        return config

    def _load_servers(self, servers_config: List[Dict[str, Any]]) -> None:
        """
        Load server specs from configuration.

        Args:
            servers_config: List of server configurations
        """
        from aethermcp.core.types import (
            MCPServerCapability,
            MCPServerSpec,
            ServerCategory,
        )

        for server_data in servers_config:
            capabilities = [
                MCPServerCapability(**cap) for cap in server_data.get("capabilities", [])
            ]

            spec = MCPServerSpec(
                name=server_data["name"],
                category=ServerCategory(server_data["category"]),
                endpoint=server_data["endpoint"],
                capabilities=capabilities,
                strengths=server_data.get("strengths", []),
                cost_per_call=server_data.get("cost_per_call", 0.0),
                auth_required=server_data.get("auth_required", True),
                metadata=server_data.get("metadata", {}),
            )

            self.registry.register(spec)

        logger.info(f"Loaded {len(servers_config)} servers from configuration")

    def _load_templates(self, templates_config: List[Dict[str, Any]]) -> None:
        """
        Load templates from configuration.

        Args:
            templates_config: List of template configurations
        """
        for template_data in templates_config:
            self.templates.register_template(template_data)

        logger.info(f"Loaded {len(templates_config)} templates from configuration")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get kernel statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "registry": self.registry.get_stats(),
            "provenance": self.provenance.get_stats(),
            "templates": self.templates.get_stats(),
        }
