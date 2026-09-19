"""
Deduplication and Collision Detection for Synthetic Datasets.
Uses SHA-256 fingerprinting on normalized text.
"""

from __future__ import annotations

import hashlib
import re
from typing import Optional, Set


class Deduplicator:
    """
    Manages in-memory text fingerprint cache to prevent duplicate samples
    from entering the synthetic training and evaluation datasets.
    """

    def __init__(self, initial_hashes: Optional[Set[str]] = None) -> None:
        self.seen_hashes: Set[str] = set(initial_hashes or set())
        self.total_seen: int = len(self.seen_hashes)
        self.total_duplicates: int = 0

    @staticmethod
    def compute_hash(text: str) -> str:
        """
        Computes SHA-256 hash of normalized text.
        Collapses whitespace to avoid duplicate semantics with minor spacing differences.
        """
        normalized = re.sub(r"\s+", " ", text.strip())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def is_duplicate(self, text: str) -> bool:
        """Returns True if the text or its hash was already recorded."""
        h = self.compute_hash(text)
        return h in self.seen_hashes

    def add(self, text: str) -> str:
        """Adds text to the deduplication index and returns its hash."""
        h = self.compute_hash(text)
        self.seen_hashes.add(h)
        self.total_seen += 1
        return h

    def add_if_unique(self, text: str) -> bool:
        """
        Checks if text is unique; if so, adds it and returns True.
        If duplicate, increments total_duplicates and returns False.
        """
        h = self.compute_hash(text)
        if h in self.seen_hashes:
            self.total_duplicates += 1
            return False
        self.seen_hashes.add(h)
        self.total_seen += 1
        return True

    def __len__(self) -> int:
        return len(self.seen_hashes)
