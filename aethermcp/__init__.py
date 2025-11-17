"""
AEF-OS v7.0 "AetherMCP"
AI Exploration Framework - Operating System
The Linux Kernel for AI Orchestration
"""

__version__ = "7.0.0"
__author__ = "Aetheris Consulting"

from aethermcp.core.kernel import AetherMCP
from aethermcp.core.orchestrator import Orchestrator
from aethermcp.core.registry import ToolRegistry
from aethermcp.core.provenance import ProvenanceEngine
from aethermcp.templates.library import TemplateLibrary

__all__ = [
    "AetherMCP",
    "Orchestrator",
    "ToolRegistry",
    "ProvenanceEngine",
    "TemplateLibrary",
]
