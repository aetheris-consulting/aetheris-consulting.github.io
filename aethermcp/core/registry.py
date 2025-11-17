"""Tool Registry - Catalog of available MCP servers."""

import logging
from typing import Dict, List, Optional

from aethermcp.core.types import MCPServerSpec, ServerCategory

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Catalog of available MCP servers.

    The registry maintains a list of all available tools (MCP servers) and their
    capabilities. The orchestrator queries this registry to discover which tools
    are available for a given task.
    """

    def __init__(self) -> None:
        """Initialize the tool registry."""
        self._servers: Dict[str, MCPServerSpec] = {}
        self._category_index: Dict[ServerCategory, List[str]] = {
            category: [] for category in ServerCategory
        }

    def register(self, spec: MCPServerSpec) -> None:
        """
        Register a new MCP server.

        Args:
            spec: Server specification
        """
        logger.info(f"Registering server: {spec.name} (category: {spec.category})")
        self._servers[spec.name] = spec

        if spec.name not in self._category_index[spec.category]:
            self._category_index[spec.category].append(spec.name)

    def unregister(self, server_name: str) -> None:
        """
        Unregister an MCP server.

        Args:
            server_name: Name of server to remove
        """
        if server_name in self._servers:
            spec = self._servers[server_name]
            self._category_index[spec.category].remove(server_name)
            del self._servers[server_name]
            logger.info(f"Unregistered server: {server_name}")

    def get_server(self, name: str) -> Optional[MCPServerSpec]:
        """
        Get server specification by name.

        Args:
            name: Server name

        Returns:
            Server spec or None if not found
        """
        return self._servers.get(name)

    def list_servers(
        self, category: Optional[ServerCategory] = None, domain: Optional[str] = None
    ) -> List[MCPServerSpec]:
        """
        List available servers, optionally filtered.

        Args:
            category: Filter by category
            domain: Filter by domain keywords in strengths

        Returns:
            List of matching server specs
        """
        servers = list(self._servers.values())

        if category:
            servers = [s for s in servers if s.category == category]

        if domain:
            domain_lower = domain.lower()
            servers = [
                s
                for s in servers
                if any(domain_lower in strength.lower() for strength in s.strengths)
            ]

        return servers

    def find_servers_for_capability(self, capability: str) -> List[MCPServerSpec]:
        """
        Find servers that provide a specific capability.

        Args:
            capability: Capability name to search for

        Returns:
            List of servers with that capability
        """
        results = []
        for server in self._servers.values():
            if any(cap.name == capability for cap in server.capabilities):
                results.append(server)
        return results

    def get_category_servers(self, category: ServerCategory) -> List[MCPServerSpec]:
        """
        Get all servers in a category.

        Args:
            category: Server category

        Returns:
            List of servers in that category
        """
        server_names = self._category_index.get(category, [])
        return [self._servers[name] for name in server_names if name in self._servers]

    def get_best_server_for_task(
        self, domain: str, required_capabilities: Optional[List[str]] = None
    ) -> Optional[MCPServerSpec]:
        """
        Find the best server for a given task.

        This implements a simple scoring algorithm that ranks servers based on:
        - Domain match (strengths overlap with domain keywords)
        - Capability match (has required capabilities)
        - Cost (lower is better)

        Args:
            domain: Task domain
            required_capabilities: List of required capability names

        Returns:
            Best matching server or None
        """
        candidates = self.list_servers(domain=domain)

        if not candidates:
            return None

        # Score each candidate
        scored = []
        for server in candidates:
            score = 0.0

            # Domain match score
            domain_words = set(domain.lower().split())
            strength_words = set(" ".join(server.strengths).lower().split())
            domain_overlap = len(domain_words & strength_words)
            score += domain_overlap * 10.0

            # Capability match score
            if required_capabilities:
                server_caps = {cap.name for cap in server.capabilities}
                cap_overlap = len(set(required_capabilities) & server_caps)
                score += cap_overlap * 20.0

                # Must have all required capabilities
                if cap_overlap < len(required_capabilities):
                    continue

            # Cost penalty (normalize to 0-10 range, assuming most calls < $1)
            cost_penalty = min(server.cost_per_call * 10, 10.0)
            score -= cost_penalty

            scored.append((score, server))

        if not scored:
            return None

        # Return highest scoring server
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1]

    def get_stats(self) -> Dict[str, int]:
        """
        Get registry statistics.

        Returns:
            Dictionary with counts by category
        """
        return {
            "total": len(self._servers),
            **{cat.value: len(servers) for cat, servers in self._category_index.items()},
        }

    def clear(self) -> None:
        """Clear all registered servers."""
        self._servers.clear()
        for category in self._category_index:
            self._category_index[category].clear()
        logger.info("Registry cleared")
