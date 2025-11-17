"""Protocol Handler - Standardized MCP communication."""

import asyncio
import logging
from typing import Any, Dict, Optional
from uuid import uuid4

import httpx
from aethermcp.core.types import MCPRequest, MCPResponse, MCPServerSpec

logger = logging.getLogger(__name__)


class ProtocolHandler:
    """
    Handles communication with MCP servers.

    Provides standardized methods for:
    - Connecting to MCP endpoints
    - Sending requests with parameters
    - Receiving and parsing responses
    - Error handling with retry logic
    """

    def __init__(self, timeout: float = 60.0, max_retries: int = 3) -> None:
        """
        Initialize protocol handler.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "ProtocolHandler":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def connect_to_server(self, spec: MCPServerSpec) -> bool:
        """
        Establish connection to an MCP endpoint.

        Args:
            spec: Server specification

        Returns:
            True if connection successful
        """
        try:
            if not self._client:
                self._client = httpx.AsyncClient(timeout=self.timeout)

            # Health check
            response = await self._client.get(f"{spec.endpoint}/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to connect to {spec.name}: {e}")
            return False

    async def send_request(
        self,
        spec: MCPServerSpec,
        tool_name: str,
        parameters: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MCPResponse:
        """
        Send request to MCP server.

        Args:
            spec: Server specification
            tool_name: Name of tool/capability to invoke
            parameters: Tool parameters
            metadata: Optional metadata

        Returns:
            MCP response
        """
        request_id = str(uuid4())
        request = MCPRequest(
            server_name=spec.name,
            tool_name=tool_name,
            parameters=parameters,
            request_id=request_id,
            metadata=metadata or {},
        )

        logger.info(f"Sending request {request_id} to {spec.name}.{tool_name}")

        for attempt in range(self.max_retries):
            try:
                response = await self._execute_request(spec, request)
                logger.info(f"Request {request_id} completed successfully")
                return response
            except Exception as e:
                logger.warning(
                    f"Request {request_id} failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)  # Exponential backoff
                else:
                    # Final attempt failed
                    return MCPResponse(
                        request_id=request_id,
                        server_name=spec.name,
                        tool_name=tool_name,
                        result=None,
                        error=str(e),
                    )

        # Should never reach here
        return MCPResponse(
            request_id=request_id,
            server_name=spec.name,
            tool_name=tool_name,
            result=None,
            error="Max retries exceeded",
        )

    async def _execute_request(
        self, spec: MCPServerSpec, request: MCPRequest
    ) -> MCPResponse:
        """
        Execute a single request (internal).

        Args:
            spec: Server specification
            request: MCP request

        Returns:
            MCP response

        Raises:
            Exception: If request fails
        """
        if not self._client:
            self._client = httpx.AsyncClient(timeout=self.timeout)

        # Construct endpoint URL
        url = f"{spec.endpoint}/tools/{request.tool_name}"

        # Send POST request
        response = await self._client.post(
            url,
            json={
                "request_id": request.request_id,
                "parameters": request.parameters,
                "metadata": request.metadata,
            },
        )

        response.raise_for_status()

        # Parse response
        data = response.json()

        return MCPResponse(
            request_id=request.request_id,
            server_name=spec.name,
            tool_name=request.tool_name,
            result=data.get("result"),
            error=data.get("error"),
            cost=data.get("cost", 0.0),
            metadata=data.get("metadata", {}),
        )

    async def send_batch_requests(
        self,
        requests: list[tuple[MCPServerSpec, str, Dict[str, Any]]],
    ) -> list[MCPResponse]:
        """
        Send multiple requests in parallel.

        Args:
            requests: List of (spec, tool_name, parameters) tuples

        Returns:
            List of responses in same order as requests
        """
        tasks = [
            self.send_request(spec, tool_name, params) for spec, tool_name, params in requests
        ]
        return await asyncio.gather(*tasks)

    def estimate_cost(self, spec: MCPServerSpec, num_calls: int = 1) -> float:
        """
        Estimate cost for calling a server.

        Args:
            spec: Server specification
            num_calls: Number of calls

        Returns:
            Estimated cost in USD
        """
        return spec.cost_per_call * num_calls

    async def close(self) -> None:
        """Close the client connection."""
        if self._client:
            await self._client.aclose()
            self._client = None
