"""Generic key-based registry for task classes.

Provides :class:`TaskRegistry`, which stores objects under unique keys,
raises :class:`ValueError` on duplicate registration or unknown lookup,
and can list the registered keys.
"""
from typing import Dict

class TaskRegistry[Key, Value]:
    """Registry for managing caetasks."""

    def __init__(self):
        self._tasks: Dict[Key, Value] = {}

    def register(self, name: Key, task: Value) -> None:
        """Register a converter by name."""
        if name in self._tasks:
            raise ValueError(f"Key '{name}' is already registered.")
        self._tasks[name] = task

    def get(self, name: Key) -> Value:
        """Get converter by name."""
        if name not in self._tasks:
            raise ValueError(f"Unknown format: {name}. Available: {list(self._tasks.keys())}")
        return self._tasks[name]

    def list_formats(self) -> list:
        """List all available formats."""
        return list(self._tasks.keys())
