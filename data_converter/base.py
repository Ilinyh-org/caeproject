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
    return 'value' in data