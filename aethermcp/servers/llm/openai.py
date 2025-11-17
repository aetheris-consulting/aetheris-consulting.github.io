"""OpenAI MCP Server implementation."""

import logging
import os
from typing import Any, Dict, List

from openai import AsyncOpenAI

from aethermcp.core.types import MCPServerCapability, ServerCategory
from aethermcp.servers.base import BaseMCPServer

logger = logging.getLogger(__name__)


class OpenAIServer(BaseMCPServer):
    """
    MCP Server for OpenAI's GPT models.

    Strengths:
    - Meta-coherence
    - Logical refinement
    - Structured thinking
    """

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o") -> None:
        """
        Initialize OpenAI server.

        Args:
            api_key: OpenAI API key (or use OPENAI_API_KEY env var)
            model: GPT model to use
        """
        super().__init__(
            name="chatgpt_server",
            category=ServerCategory.LLM,
            endpoint="https://api.openai.com/v1",
            strengths=["meta_coherence", "logical_refinement", "structured_thinking"],
            cost_per_call=0.010,  # Approximate for GPT-4
        )

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None

    def get_capabilities(self) -> List[MCPServerCapability]:
        """Get OpenAI capabilities."""
        return [
            MCPServerCapability(
                name="generate",
                description="Generate text completion",
                parameters={
                    "prompt": "string - The prompt to complete",
                    "temperature": "float - Sampling temperature (0-2)",
                    "max_tokens": "int - Maximum tokens to generate",
                },
                returns={"text": "string - Generated text", "usage": "object - Token usage"},
            ),
            MCPServerCapability(
                name="refine_logic",
                description="Refine logical structure of argument",
                parameters={
                    "argument": "string - Argument to refine",
                    "constraints": "array - Logical constraints",
                },
                returns={
                    "refined": "string - Refined argument",
                    "issues_found": "array - Logical issues corrected",
                },
            ),
        ]

    async def handle_request(
        self, tool_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle OpenAI MCP request."""
        if not self.client:
            return {
                "result": None,
                "error": "OpenAI API key not configured",
                "cost": 0.0,
                "metadata": {},
            }

        try:
            if tool_name == "generate":
                return await self._handle_generate(parameters)
            elif tool_name == "refine_logic":
                return await self._handle_refine_logic(parameters)
            else:
                return {
                    "result": None,
                    "error": f"Unknown tool: {tool_name}",
                    "cost": 0.0,
                    "metadata": {},
                }
        except Exception as e:
            logger.error(f"OpenAI request failed: {e}", exc_info=True)
            return {"result": None, "error": str(e), "cost": 0.0, "metadata": {}}

    async def _handle_generate(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generate request."""
        prompt = parameters.get("prompt", "")
        temperature = parameters.get("temperature", 0.7)
        max_tokens = parameters.get("max_tokens", 1024)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Calculate cost (GPT-4 pricing)
        usage = response.usage
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens
        cost = (input_tokens * 0.00001) + (output_tokens * 0.00003)  # GPT-4 pricing

        return {
            "result": {
                "text": response.choices[0].message.content,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                },
            },
            "error": None,
            "cost": cost,
            "metadata": {"model": self.model},
        }

    async def _handle_refine_logic(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle logic refinement request."""
        argument = parameters.get("argument", "")
        constraints = parameters.get("constraints", [])

        constraints_str = "\n".join(f"- {c}" for c in constraints)
        prompt = f"""Refine the logical structure of the following argument:

{argument}

Constraints:
{constraints_str}

Provide:
1. Refined version with improved logical flow
2. List of logical issues you corrected
3. Confidence in the refinement

Format as JSON."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2048,
        )

        # Calculate cost
        usage = response.usage
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens
        cost = (input_tokens * 0.00001) + (output_tokens * 0.00003)

        return {
            "result": {
                "refinement": response.choices[0].message.content,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                },
            },
            "error": None,
            "cost": cost,
            "metadata": {"model": self.model},
        }
