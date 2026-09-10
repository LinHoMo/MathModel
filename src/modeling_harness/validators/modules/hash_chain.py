"""L6: Hash Chain - SHA-256 hash chain for intermediate artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class HashEntry:
    index: int
    artifact_name: str
    data_hash: str
    previous_hash: str
    chain_hash: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


class HashChain:
    """SHA-256 hash chain for all intermediate artifacts.

    Provides tamper detection by chaining hashes of artifacts. Each entry
    includes the hash of the previous entry, forming an immutable chain.
    """

    def __init__(self) -> None:
        self._chain: List[HashEntry] = []
        self._audit_log: List[Dict[str, Any]] = []

    def compute_hash(self, data: Any) -> str:
        """Compute SHA-256 hash of arbitrary data.

        Data is JSON-serialized before hashing for consistency.
        """
        if isinstance(data, str):
            serialized = data
        else:
            serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def add_entry(
        self,
        artifact_name: str,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> HashEntry:
        """Add a new entry to the hash chain.

        Args:
            artifact_name: Name/identifier of the artifact.
            data: The data to hash.
            metadata: Optional metadata to store with the entry.

        Returns:
            The created HashEntry.
        """
        previous_hash = self._chain[-1].chain_hash if self._chain else "0" * 64
        data_hash = self.compute_hash(data)
        chain_input = f"{previous_hash}{data_hash}"
        chain_hash = hashlib.sha256(chain_input.encode("utf-8")).hexdigest()

        entry = HashEntry(
            index=len(self._chain),
            artifact_name=artifact_name,
            data_hash=data_hash,
            previous_hash=previous_hash,
            chain_hash=chain_hash,
            metadata=metadata or {},
        )
        self._chain.append(entry)

        self._audit_log.append({
            "action": "add_entry",
            "index": entry.index,
            "artifact": artifact_name,
            "timestamp": entry.timestamp,
        })

        return entry

    def verify_chain(self) -> bool:
        """Verify the integrity of the entire hash chain.

        Returns True if the chain is valid (no tampering detected).
        """
        for i, entry in enumerate(self._chain):
            expected_prev = self._chain[i - 1].chain_hash if i > 0 else "0" * 64
            if entry.previous_hash != expected_prev:
                return False

            chain_input = f"{entry.previous_hash}{entry.data_hash}"
            expected_chain = hashlib.sha256(chain_input.encode("utf-8")).hexdigest()
            if entry.chain_hash != expected_chain:
                return False

        return True

    def verify_entry(self, index: int, original_data: Any) -> bool:
        """Verify a specific entry against original data."""
        if index < 0 or index >= len(self._chain):
            return False
        entry = self._chain[index]
        computed_hash = self.compute_hash(original_data)
        return entry.data_hash == computed_hash

    def get_entry(self, index: int) -> Optional[HashEntry]:
        """Get a hash chain entry by index."""
        if 0 <= index < len(self._chain):
            return self._chain[index]
        return None

    def get_chain_length(self) -> int:
        """Return the current length of the hash chain."""
        return len(self._chain)

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Return the full audit log of chain operations."""
        return list(self._audit_log)

    def get_artifacts(self) -> List[str]:
        """Return names of all artifacts in the chain."""
        return [entry.artifact_name for entry in self._chain]

    def to_dict(self) -> List[Dict[str, Any]]:
        """Serialize the chain to a list of dictionaries."""
        return [
            {
                "index": e.index,
                "artifact_name": e.artifact_name,
                "data_hash": e.data_hash,
                "previous_hash": e.previous_hash,
                "chain_hash": e.chain_hash,
                "timestamp": e.timestamp,
                "metadata": e.metadata,
            }
            for e in self._chain
        ]


def create_hash_chain() -> HashChain:
    """Convenience: create an empty hash chain."""
    return HashChain()
