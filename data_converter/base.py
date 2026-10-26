"""Data converter interface and shared helpers.

Defines the :class:`DataConverter` abstract base class every format
converter implements and the :func:`is_parameter` predicate used to
recognize unit-aware parameter dictionaries.
"""
from typing import Dict, Any
from abc import ABC, abstractmethod


class DataConverter(ABC):
    """Abstract base class for data converters."""

    @abstractmethod
    def convert(self, data: Dict[str, Any]) -> str:
        """Convert dictionary data to string representation."""
        pass

    @abstractmethod
    def get_extension(self) -> str:
        """Get file extension for this format."""
        pass


def is_parameter(data: dict):
    """Return True if the dict looks like a parameter (has a 'value' key)."""
    return 'value' in data