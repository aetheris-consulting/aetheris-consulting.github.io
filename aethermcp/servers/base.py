"""Base class for MCP servers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from aethermcp.core.types import MCPServerCapability, MCPServerSpec, ServerCategory


class BaseMCPServer(ABC):
    """
    Base class for all MCP servers.

    Subclasses must implement the capabilities they provide and the
    handle_request method to process incoming MCP requests.
    """

    def __init__(
        self,
        name: str,
        category: ServerCategory,
        endpoint: str,
        strengths: List[str],
        cost_per_call: float = 0.0,
    ) -> None:
        """
        Initialize MCP server.

        Args:
            name: Server name
            category: Server category
            endpoint: API endpoint
            strengths: List of strengths/specializations
            cost_per_call: Average cost per call in USD
        """
        self.name = name
        self.category = category
        self.endpoint = endpoint
        self.strengths = strengths
        self.cost_per_call = cost_per_call

    @abstractmethod
    def get_capabilities(self) -> List[MCPServerCapability]:
        """
        Get list of capabilities this server provides.

        Returns:
            List of capability specifications
        """
        pass

    @abstractmethod
    async def handle_request(
        self, tool_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle an MCP request.

        Args:
            tool_name: Name of tool to invoke
            parameters: Tool parameters

        Returns:
            Response dictionary with 'result', 'error', 'cost', 'metadata' keys
        """
        pass

    def get_spec(self) -> MCPServerSpec:
        """
        Get MCP server specification.

        Returns:
            Server spec
        """
        return MCPServerSpec(
            name=self.name,
            category=self.category,
            endpoint=self.endpoint,
            capabilities=self.get_capabilities(),
            strengths=self.strengths,
            cost_per_call=self.cost_per_call,
        )

    async def health_check(self) -> bool:
        """
        Check if server is healthy.

        Returns:
            True if server is operational
        """
        return True
