"""Data model layer for GC log analysis.

Provides GCPhase representation used by the JDK 8 G1 multi-line state machine.
"""

from dataclasses import dataclass


@dataclass
class GCPhase:
    """A single phase within a GC event (e.g., Object Copy, Ext Root Scanning)."""
    name: str
    duration_ms: float
