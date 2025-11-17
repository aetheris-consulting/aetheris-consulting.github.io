"""Claude MCP Server implementation."""

import logging
import os
from typing import Any, Dict, List

from anthropic import AsyncAnthropic

from aethermcp.core.types import MCPServerCapability, ServerCategory
from aethermcp.servers.base import BaseMCPServer

logger = logging.getLogger(__name__)


class ClaudeServer(BaseMCPServer):
    """
    MCP Server for Anthropic's Claude models.

    Strengths:
    - Validation rigor
    - Security analysis
    - Ethical reasoning
    """

    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-4-5-20250929") -> None:
        """
        Initialize Claude server.

        Args:
            api_key: Anthropic API key (or use ANTHROPIC_API_KEY env var)
            model: Claude model to use
        """
        super().__init__(
            name="claude_server",
            category=ServerCategory.LLM,
            endpoint="https://api.anthropic.com/v1",
            strengths=["validation_rigor", "security_analysis", "ethical_reasoning"],
            cost_per_call=0.015,  # Approximate for Sonnet
        )

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.client = AsyncAnthropic(api_key=self.api_key) if self.api_key else None

    def get_capabilities(self) -> List[MCPServerCapability]:
        """Get Claude capabilities."""
        return [
            MCPServerCapability(
                name="generate",
                description="Generate text completion",
                parameters={
                    "prompt": "string - The prompt to complete",
                    "temperature": "float - Sampling temperature (0-1)",
                    "max_tokens": "int - Maximum tokens to generate",
                },
                returns={"text": "string - Generated text", "usage": "object - Token usage"},
            ),
            MCPServerCapability(
                name="analyze_security",
                description="Analyze security vulnerabilities",
                parameters={
                    "code": "string - Code to analyze",
                    "context": "string - Additional context",
                },
                returns={
                    "vulnerabilities": "array - List of vulnerabilities found",
                    "severity": "string - Overall severity rating",
                },
            ),
            MCPServerCapability(
                name="validate_design",
                description="Validate design against best practices",
                parameters={
                    "design": "string - Design specification",
                    "domain": "string - Domain (security, safety, etc)",
                },
                returns={
                    "is_valid": "boolean - Whether design is valid",
                    "issues": "array - List of issues found",
                    "recommendations": "array - Recommendations",
                },
            ),
        ]

    async def handle_request(
        self, tool_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle Claude MCP request."""
        if not self.client:
            return {
                "result": None,
                "error": "Claude API key not configured",
                "cost": 0.0,
                "metadata": {},
            }

        try:
            if tool_name == "generate":
                return await self._handle_generate(parameters)
            elif tool_name == "analyze_security":
                return await self._handle_analyze_security(parameters)
            elif tool_name == "validate_design":
                return await self._handle_validate_design(parameters)
            else:
                return {
                    "result": None,
                    "error": f"Unknown tool: {tool_name}",
                    "cost": 0.0,
                    "metadata": {},
                }
        except Exception as e:
            logger.error(f"Claude request failed: {e}", exc_info=True)
            return {"result": None, "error": str(e), "cost": 0.0, "metadata": {}}

    async def _handle_generate(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generate request."""
        prompt = parameters.get("prompt", "")
        temperature = parameters.get("temperature", 0.7)
        max_tokens = parameters.get("max_tokens", 1024)

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        # Calculate cost (rough estimate)
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = (input_tokens * 0.000003) + (output_tokens * 0.000015)  # Sonnet pricing

        return {
            "result": {
                "text": response.content[0].text,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                },
            },
            "error": None,
            "cost": cost,
            "metadata": {"model": self.model},
        }

    async def _handle_analyze_security(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle security analysis request."""
        code = parameters.get("code", "")
        context = parameters.get("context", "")

        prompt = f"""Analyze the following code for security vulnerabilities:

Context: {context}

Code:
```
{code}
```

Provide a detailed security analysis including:
1. List of vulnerabilities found
2. Severity rating for each
3. Mitigation recommendations

Format as JSON."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            temperature=0.3,  # Lower temperature for analytical tasks
            messages=[{"role": "user", "content": prompt}],
        )

        # Calculate cost
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = (input_tokens * 0.000003) + (output_tokens * 0.000015)

        return {
            "result": {
                "analysis": response.content[0].text,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                },
            },
            "error": None,
            "cost": cost,
            "metadata": {"model": self.model},
        }

    async def _handle_validate_design(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle design validation request."""
        design = parameters.get("design", "")
        domain = parameters.get("domain", "general")

        prompt = f"""Validate the following design for {domain} domain:

{design}

Provide:
1. Overall validity assessment
2. List of issues/concerns
3. Recommendations for improvement

Format as JSON."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )

        # Calculate cost
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = (input_tokens * 0.000003) + (output_tokens * 0.000015)

        return {
            "result": {
                "validation": response.content[0].text,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                },
            },
            "error": None,
            "cost": cost,
            "metadata": {"model": self.model},
        }
