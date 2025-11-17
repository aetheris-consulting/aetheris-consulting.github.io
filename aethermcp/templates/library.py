"""Template Library - Reusable workflow patterns."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from aethermcp.core.types import TemplateSpec

logger = logging.getLogger(__name__)


class TemplateLibrary:
    """
    Library of reusable workflow templates.

    Templates capture proven methodologies that worked well in the past,
    allowing AIs to suggest them when applicable without enforcing rigidity.
    """

    def __init__(self) -> None:
        """Initialize template library."""
        self._templates: Dict[str, TemplateSpec] = {}
        self._load_builtin_templates()

    def register_template(self, template_data: Dict[str, Any]) -> None:
        """
        Register a new template.

        Args:
            template_data: Template specification
        """
        template = TemplateSpec(**template_data)
        self._templates[template.name] = template
        logger.info(f"Registered template: {template.name}")

    def get_template(self, name: str) -> Optional[TemplateSpec]:
        """
        Get template by name.

        Args:
            name: Template name

        Returns:
            Template spec or None if not found
        """
        return self._templates.get(name)

    def list_templates(self) -> List[TemplateSpec]:
        """
        List all available templates.

        Returns:
            List of template specs
        """
        return list(self._templates.values())

    def suggest_templates(self, keywords: List[str]) -> List[TemplateSpec]:
        """
        Suggest templates based on keywords.

        Args:
            keywords: List of keywords to match

        Returns:
            List of matching templates
        """
        results = []
        keywords_lower = [kw.lower() for kw in keywords]

        for template in self._templates.values():
            # Check if any keyword matches template name, description, or when_to_use
            searchable = f"{template.name} {template.description} {template.when_to_use}".lower()

            if any(kw in searchable for kw in keywords_lower):
                results.append(template)

        return results

    def load_from_directory(self, directory: str) -> int:
        """
        Load templates from YAML files in a directory.

        Args:
            directory: Path to directory containing template files

        Returns:
            Number of templates loaded
        """
        path = Path(directory)
        if not path.exists():
            logger.warning(f"Template directory not found: {directory}")
            return 0

        count = 0
        for file_path in path.glob("*.yaml"):
            try:
                with open(file_path) as f:
                    template_data = yaml.safe_load(f)
                    self.register_template(template_data)
                    count += 1
            except Exception as e:
                logger.error(f"Failed to load template from {file_path}: {e}")

        logger.info(f"Loaded {count} templates from {directory}")
        return count

    def _load_builtin_templates(self) -> None:
        """Load built-in templates."""

        # Multi-AI Brainstorm Template
        self.register_template(
            {
                "name": "multi_ai_brainstorm_template",
                "description": "Generate diverse ideas using multiple LLMs",
                "when_to_use": "Need diverse ideas for novel problem, exploratory research",
                "steps": [
                    {
                        "name": "parallel_generation",
                        "description": "Run 3+ LLMs independently for idea generation",
                        "servers": ["claude_server", "chatgpt_server", "gemini_server"],
                        "tool": "generate_ideas",
                        "parameters": {"temperature": 0.9},
                        "parallel": True,
                    },
                    {
                        "name": "synthesis",
                        "description": "Merge and deduplicate results",
                        "servers": ["synthesizer"],
                        "tool": "merge_deduplicate",
                        "parameters": {},
                        "parallel": False,
                    },
                ],
                "success_criteria": ["Entropy > 0.18", "At least 10 unique ideas"],
            }
        )

        # Security Validation Template
        self.register_template(
            {
                "name": "security_validation_template",
                "description": "Comprehensive security testing and validation",
                "when_to_use": "Design requires adversarial testing, security is critical",
                "steps": [
                    {
                        "name": "enumerate_threats",
                        "description": "Systematically enumerate threats using STRIDE + FMEA",
                        "servers": ["threat_modeler"],
                        "tool": "enumerate",
                        "parameters": {"method": "STRIDE"},
                        "parallel": False,
                    },
                    {
                        "name": "test_scenarios",
                        "description": "Test attack scenarios via simulation",
                        "servers": ["network_simulator"],
                        "tool": "test_attacks",
                        "parameters": {},
                        "parallel": True,
                    },
                    {
                        "name": "validate_standards",
                        "description": "Validate against security standards",
                        "servers": ["security_validator"],
                        "tool": "check_owasp",
                        "parameters": {},
                        "parallel": False,
                    },
                ],
                "success_criteria": [
                    ">90% coverage of known attack vectors",
                    "All OWASP Top 10 checks passed",
                ],
            }
        )

        # Calibrated Scoring Template
        self.register_template(
            {
                "name": "calibrated_scoring_template",
                "description": "High-fidelity validation using ground truth",
                "when_to_use": "Need >0.80 confidence, high-stakes decision, validation required",
                "steps": [
                    {
                        "name": "load_ground_truth",
                        "description": "Load validated data for calibration",
                        "servers": ["data_server"],
                        "tool": "load_ground_truth",
                        "parameters": {},
                        "parallel": False,
                    },
                    {
                        "name": "calibrate",
                        "description": "Test against known outcomes",
                        "servers": ["validator"],
                        "tool": "calibrate_against_known_outcomes",
                        "parameters": {},
                        "parallel": False,
                    },
                    {
                        "name": "score",
                        "description": "Compute OGM scores",
                        "servers": ["scoring_engine"],
                        "tool": "compute_ogm",
                        "parameters": {},
                        "parallel": False,
                    },
                    {
                        "name": "propagate_uncertainty",
                        "description": "Track confidence through pipeline",
                        "servers": ["uncertainty_tracker"],
                        "tool": "propagate_confidence",
                        "parameters": {},
                        "parallel": False,
                    },
                ],
                "success_criteria": ["OGM score > 0.80", "Confidence > 0.85"],
            }
        )

        # Systematic Enumeration Template
        self.register_template(
            {
                "name": "systematic_enumeration_template",
                "description": "Comprehensive coverage using structured methodology",
                "when_to_use": "High-stakes domain (security, safety, health)",
                "steps": [
                    {
                        "name": "stride_analysis",
                        "description": "Apply STRIDE for security threats",
                        "servers": ["threat_modeler"],
                        "tool": "stride_analysis",
                        "parameters": {},
                        "parallel": False,
                    },
                    {
                        "name": "fmea_analysis",
                        "description": "Apply FMEA for failure modes",
                        "servers": ["failure_analyzer"],
                        "tool": "fmea_analysis",
                        "parameters": {},
                        "parallel": False,
                    },
                    {
                        "name": "compute_coverage",
                        "description": "Calculate coverage percentage",
                        "servers": ["coverage_reporter"],
                        "tool": "compute_percentage",
                        "parameters": {},
                        "parallel": False,
                    },
                ],
                "success_criteria": [">90% coverage of known failure modes"],
            }
        )

        # Cost Constrained Execution Template
        self.register_template(
            {
                "name": "cost_constrained_execution_template",
                "description": "Execute within budget limits",
                "when_to_use": "Budget limits require optimization, cost-sensitive operation",
                "steps": [
                    {
                        "name": "set_budget",
                        "description": "Set session budget",
                        "servers": ["cost_tracker"],
                        "tool": "set_budget",
                        "parameters": {},
                        "parallel": False,
                    },
                    {
                        "name": "monitor_spend",
                        "description": "Real-time cost tracking",
                        "servers": ["cost_tracker"],
                        "tool": "monitor_spend",
                        "parameters": {"real_time": True},
                        "parallel": False,
                    },
                ],
                "success_criteria": ["Total cost <= budget", "No budget overruns"],
            }
        )

        # Replication Package Template
        self.register_template(
            {
                "name": "replication_package_template",
                "description": "Create reproducible research package",
                "when_to_use": "Scientific reproducibility required, auditing needed",
                "steps": [
                    {
                        "name": "capture_state",
                        "description": "Record all parameters and settings",
                        "servers": ["state_capturer"],
                        "tool": "record_all_params",
                        "parameters": {},
                        "parallel": False,
                    },
                    {
                        "name": "snapshot_data",
                        "description": "Hash all data sources used",
                        "servers": ["data_snapshot"],
                        "tool": "compute_hash",
                        "parameters": {},
                        "parallel": False,
                    },
                    {
                        "name": "package",
                        "description": "Create container with state + data + script",
                        "servers": ["packager"],
                        "tool": "create_container",
                        "parameters": {},
                        "parallel": False,
                    },
                ],
                "success_criteria": ["Package can be executed to reproduce results"],
            }
        )

        logger.info("Loaded built-in templates")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get template library statistics.

        Returns:
            Statistics dictionary
        """
        return {"total_templates": len(self._templates), "templates": list(self._templates.keys())}
