"""Provenance Engine - Immutable audit trail with cryptographic verification."""

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from aethermcp.core.types import ProvenanceChain, ProvenanceNode

logger = logging.getLogger(__name__)


class ProvenanceEngine:
    """
    Tracks complete audit trail of all decisions and actions.

    Provides immutable, cryptographically verified record of:
    - User intent
    - Orchestration plans
    - MCP server calls
    - Results and synthesis
    - Cost tracking
    - Confidence propagation
    """

    def __init__(self) -> None:
        """Initialize provenance engine."""
        self._chains: Dict[str, ProvenanceChain] = {}

    def create_session(self, session_id: Optional[str] = None) -> str:
        """
        Create a new provenance chain for a session.

        Args:
            session_id: Optional session ID (generated if not provided)

        Returns:
            Session ID
        """
        if session_id is None:
            session_id = str(uuid4())

        # Create genesis node
        genesis = ProvenanceNode(
            node_id=f"{session_id}_genesis",
            node_type="genesis",
            timestamp=datetime.utcnow(),
            data={"session_id": session_id, "created_at": datetime.utcnow().isoformat()},
            parent_ids=[],
        )
        genesis.hash = self._compute_hash(genesis)

        # Create chain
        chain = ProvenanceChain(
            session_id=session_id, nodes=[genesis], root_hash=genesis.hash
        )

        self._chains[session_id] = chain
        logger.info(f"Created provenance chain for session {session_id}")
        return session_id

    def record_intent(
        self, session_id: str, intent_data: Dict[str, Any], parent_id: Optional[str] = None
    ) -> str:
        """
        Record user intent.

        Args:
            session_id: Session ID
            intent_data: Intent information
            parent_id: Optional parent node ID

        Returns:
            Node ID
        """
        return self._add_node(
            session_id=session_id,
            node_type="intent",
            data=intent_data,
            parent_id=parent_id or f"{session_id}_genesis",
        )

    def record_plan(
        self, session_id: str, plan_data: Dict[str, Any], parent_id: str
    ) -> str:
        """
        Record orchestration plan.

        Args:
            session_id: Session ID
            plan_data: Plan information
            parent_id: Parent node ID (typically intent node)

        Returns:
            Node ID
        """
        return self._add_node(
            session_id=session_id, node_type="plan", data=plan_data, parent_id=parent_id
        )

    def record_step(
        self, session_id: str, step_data: Dict[str, Any], parent_id: str
    ) -> str:
        """
        Record execution step (MCP call).

        Args:
            session_id: Session ID
            step_data: Step information (request, response, cost, etc.)
            parent_id: Parent node ID (typically plan node)

        Returns:
            Node ID
        """
        return self._add_node(
            session_id=session_id, node_type="step", data=step_data, parent_id=parent_id
        )

    def record_result(
        self, session_id: str, result_data: Dict[str, Any], parent_id: str
    ) -> str:
        """
        Record execution result.

        Args:
            session_id: Session ID
            result_data: Result information
            parent_id: Parent node ID (typically step node)

        Returns:
            Node ID
        """
        return self._add_node(
            session_id=session_id, node_type="result", data=result_data, parent_id=parent_id
        )

    def record_synthesis(
        self, session_id: str, synthesis_data: Dict[str, Any], parent_ids: List[str]
    ) -> str:
        """
        Record synthesis of multiple results.

        Args:
            session_id: Session ID
            synthesis_data: Synthesis information
            parent_ids: List of parent node IDs being synthesized

        Returns:
            Node ID
        """
        node_id = f"{session_id}_{str(uuid4())}"
        chain = self._chains.get(session_id)

        if not chain:
            raise ValueError(f"Session {session_id} not found")

        node = ProvenanceNode(
            node_id=node_id,
            node_type="synthesis",
            timestamp=datetime.utcnow(),
            data=synthesis_data,
            parent_ids=parent_ids,
        )
        node.hash = self._compute_hash(node)

        chain.nodes.append(node)
        logger.debug(f"Recorded synthesis node {node_id} for session {session_id}")
        return node_id

    def get_chain(self, session_id: str) -> Optional[ProvenanceChain]:
        """
        Get provenance chain for a session.

        Args:
            session_id: Session ID

        Returns:
            Provenance chain or None if not found
        """
        return self._chains.get(session_id)

    def verify_chain(self, session_id: str) -> bool:
        """
        Verify integrity of provenance chain.

        Checks that all cryptographic hashes are valid and chain is unbroken.

        Args:
            session_id: Session ID

        Returns:
            True if chain is valid
        """
        chain = self._chains.get(session_id)
        if not chain:
            return False

        # Verify each node
        for node in chain.nodes:
            expected_hash = self._compute_hash(node)
            if node.hash != expected_hash:
                logger.error(f"Hash mismatch for node {node.node_id}")
                return False

            # Verify parent references exist
            for parent_id in node.parent_ids:
                parent_exists = any(n.node_id == parent_id for n in chain.nodes)
                if not parent_exists:
                    logger.error(f"Parent {parent_id} not found for node {node.node_id}")
                    return False

        # Verify root hash
        if chain.nodes:
            genesis = chain.nodes[0]
            if genesis.hash != chain.root_hash:
                logger.error("Root hash mismatch")
                return False

        logger.info(f"Provenance chain {session_id} verified successfully")
        return True

    def export_chain(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Export provenance chain as JSON.

        Args:
            session_id: Session ID

        Returns:
            Chain data as dictionary
        """
        chain = self._chains.get(session_id)
        if not chain:
            return None

        return json.loads(chain.model_dump_json())

    def import_chain(self, chain_data: Dict[str, Any]) -> bool:
        """
        Import provenance chain from JSON.

        Args:
            chain_data: Chain data dictionary

        Returns:
            True if import successful
        """
        try:
            chain = ProvenanceChain(**chain_data)
            self._chains[chain.session_id] = chain

            # Verify after import
            if self.verify_chain(chain.session_id):
                logger.info(f"Imported and verified chain {chain.session_id}")
                return True
            else:
                logger.error(f"Imported chain {chain.session_id} failed verification")
                del self._chains[chain.session_id]
                return False
        except Exception as e:
            logger.error(f"Failed to import chain: {e}")
            return False

    def get_node_lineage(self, session_id: str, node_id: str) -> List[ProvenanceNode]:
        """
        Get all ancestors of a node (walk backwards through parents).

        Args:
            session_id: Session ID
            node_id: Node ID

        Returns:
            List of nodes from genesis to specified node
        """
        chain = self._chains.get(session_id)
        if not chain:
            return []

        # Build node lookup
        node_map = {node.node_id: node for node in chain.nodes}

        # Walk backwards from target node
        lineage = []
        visited = set()
        queue = [node_id]

        while queue:
            current_id = queue.pop(0)
            if current_id in visited:
                continue

            visited.add(current_id)
            node = node_map.get(current_id)
            if node:
                lineage.append(node)
                queue.extend(node.parent_ids)

        # Reverse to get chronological order
        lineage.reverse()
        return lineage

    def compute_session_cost(self, session_id: str) -> float:
        """
        Compute total cost from all recorded steps.

        Args:
            session_id: Session ID

        Returns:
            Total cost in USD
        """
        chain = self._chains.get(session_id)
        if not chain:
            return 0.0

        total = 0.0
        for node in chain.nodes:
            if node.node_type == "step" and "cost" in node.data:
                total += node.data["cost"]

        return total

    def _add_node(
        self,
        session_id: str,
        node_type: str,
        data: Dict[str, Any],
        parent_id: str,
    ) -> str:
        """
        Add a node to the provenance chain (internal).

        Args:
            session_id: Session ID
            node_type: Type of node
            data: Node data
            parent_id: Parent node ID

        Returns:
            Node ID
        """
        node_id = f"{session_id}_{str(uuid4())}"
        chain = self._chains.get(session_id)

        if not chain:
            raise ValueError(f"Session {session_id} not found")

        node = ProvenanceNode(
            node_id=node_id,
            node_type=node_type,
            timestamp=datetime.utcnow(),
            data=data,
            parent_ids=[parent_id],
        )
        node.hash = self._compute_hash(node)

        chain.nodes.append(node)
        logger.debug(f"Recorded {node_type} node {node_id} for session {session_id}")
        return node_id

    def _compute_hash(self, node: ProvenanceNode) -> str:
        """
        Compute cryptographic hash of a node.

        Args:
            node: Provenance node

        Returns:
            SHA-256 hash
        """
        # Create deterministic representation
        content = {
            "node_id": node.node_id,
            "node_type": node.node_type,
            "timestamp": node.timestamp.isoformat(),
            "data": node.data,
            "parent_ids": sorted(node.parent_ids),
        }

        # Compute hash
        content_json = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_json.encode()).hexdigest()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get provenance engine statistics.

        Returns:
            Statistics dictionary
        """
        total_nodes = sum(len(chain.nodes) for chain in self._chains.values())
        return {
            "total_sessions": len(self._chains),
            "total_nodes": total_nodes,
            "sessions": [
                {
                    "session_id": session_id,
                    "nodes": len(chain.nodes),
                    "created": chain.created_at.isoformat(),
                }
                for session_id, chain in self._chains.items()
            ],
        }
