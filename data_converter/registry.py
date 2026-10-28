"""Name-based registry for data converters.

Provides :class:`ConverterRegistry`, which stores converters under
unique format names, raises :class:`ValueError` for unknown names,
and can list the registered formats.
"""

from . import DataConverter

class ConverterRegistry:
    """Registry for managing data converters."""

    def __init__(self):
        self._converters: dict[str, DataConverter] = {}

    def register(self, name: str, converter: DataConverter):
        """Register a converter by name."""
        self._converters[name] = converter

    def get(self, name: str) -> DataConverter:
        """Get converter by name."""
        if name not in self._converters:
            raise ValueError(f"Unknown format: {name}. Available: {list(self._converters.keys())}")
        return self._converters[name]

    def list_formats(self) -> list:
        """List all available formats."""
        return list(self._converters.keys())
