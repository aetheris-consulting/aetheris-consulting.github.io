"""Type definitions for AetherMCP."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Status of a task in the orchestration pipeline."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ServerCategory(str, Enum):
    """Categories of MCP servers."""

    LLM = "llm_servers"
    SIMULATION = "simulation_servers"
    DATA = "data_servers"
    VALIDATION = "validation_servers"
    UTILITY = "utility_servers"


class ExecutionMode(str, Enum):
    """Execution modes for the orchestrator."""

    NARROW = "narrow"  # Conservative, high-precision
    FREEFIELD = "freefield"  # Exploratory, high-diversity


class ConfidenceLevel(str, Enum):
    """Confidence levels for validation."""

    LOW = "low"  # < 0.70
    MEDIUM = "medium"  # 0.70 - 0.85
    HIGH = "high"  # 0.85 - 0.95
    VERY_HIGH = "very_high"  # > 0.95


# ============================================================
# Intent and Planning Types
# ============================================================


class UserIntent(BaseModel):
    """Parsed user intent."""

    raw_input: str = Field(..., description="Original user request")
    primary_objective: str = Field(..., description="Main goal to achieve")
    domain: str = Field(..., description="Problem domain")
    constraints: List[str] = Field(default_factory=list, description="Requirements and limits")
    success_criteria: List[str] = Field(
        default_factory=list, description="How to measure success"
    )
    budget: Optional[float] = Field(None, description="Cost limit in USD")
    mode: ExecutionMode = Field(
        default=ExecutionMode.NARROW, description="Execution strategy"
    )


class OrchestrationPlan(BaseModel):
    """Execution plan for fulfilling intent."""

    intent: UserIntent
    steps: List["OrchestrationStep"]
    estimated_cost: float = Field(default=0.0, description="Predicted cost in USD")
    estimated_time: float = Field(default=0.0, description="Predicted time in seconds")
    confidence: float = Field(default=0.0, description="Confidence in plan (0-1)")
    templates_used: List[str] = Field(default_factory=list)


class OrchestrationStep(BaseModel):
    """A single step in the orchestration plan."""

    step_id: str
    description: str
    server_name: str
    tool_name: str
    parameters: Dict[str, Any]
    dependencies: List[str] = Field(default_factory=list)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    parallel_group: Optional[int] = Field(None, description="Steps with same ID run in parallel")


# ============================================================
# MCP Server Types
# ============================================================


class MCPServerCapability(BaseModel):
    """Description of what an MCP server can do."""

    name: str
    description: str
    parameters: Dict[str, Any]
    returns: Dict[str, Any]


class MCPServerSpec(BaseModel):
    """Specification for an MCP server."""

    name: str
    category: ServerCategory
    endpoint: str
    capabilities: List[MCPServerCapability]
    strengths: List[str] = Field(default_factory=list)
    cost_per_call: float = Field(default=0.0, description="Average cost in USD")
    auth_required: bool = Field(default=True)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MCPRequest(BaseModel):
    """Request to an MCP server."""

    server_name: str
    tool_name: str
    parameters: Dict[str, Any]
    request_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MCPResponse(BaseModel):
    """Response from an MCP server."""

    request_id: str
    server_name: str
    tool_name: str
    result: Any
    error: Optional[str] = None
    cost: float = Field(default=0.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================
# Provenance Types
# ============================================================


class ProvenanceNode(BaseModel):
    """A node in the provenance DAG."""

    node_id: str
    node_type: str  # "intent", "plan", "step", "result", "synthesis"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any]
    parent_ids: List[str] = Field(default_factory=list)
    hash: str = Field(default="", description="Cryptographic hash")


class ProvenanceChain(BaseModel):
    """Complete provenance chain for a session."""

    session_id: str
    nodes: List[ProvenanceNode]
    root_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================
# Execution Result Types
# ============================================================


class ExecutionResult(BaseModel):
    """Result of executing an orchestration plan."""

    session_id: str
    intent: UserIntent
    deliverables: Dict[str, Any] = Field(
        default_factory=dict, description="Output artifacts"
    )
    provenance: ProvenanceChain
    cost: float = Field(default=0.0, description="Total cost in USD")
    time_elapsed: float = Field(default=0.0, description="Execution time in seconds")
    confidence: float = Field(default=0.0, description="Overall confidence (0-1)")
    status: TaskStatus
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================
# Template Types
# ============================================================


class TemplateSpec(BaseModel):
    """Template for reusable workflows."""

    name: str
    description: str
    when_to_use: str
    steps: List[Dict[str, Any]]
    parameters: Dict[str, Any] = Field(default_factory=dict)
    success_criteria: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================
# Governance Types
# ============================================================


class AlertLevel(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class GovernanceAlert(BaseModel):
    """Alert from governance system."""

    alert_id: str
    level: AlertLevel
    message: str
    source: str  # "cognitive_guardian", "sentinel", "cost_tracker", etc.
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    requires_action: bool = Field(default=False)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OperatorProfile(BaseModel):
    """Behavioral profile of an operator."""

    operator_id: str
    selection_patterns: Dict[str, float] = Field(default_factory=dict)
    risk_tolerance: float = Field(default=0.5, description="0 = conservative, 1 = aggressive")
    testing_style: Dict[str, Any] = Field(default_factory=dict)
    baseline_deviation: float = Field(default=0.0, description="Sigma from historical behavior")


# Forward refs
OrchestrationPlan.model_rebuild()
