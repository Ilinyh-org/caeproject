from typing import Dict

from core.converter import DataConverter
from core.converter import JSONConverter
from core.converter import APDLConverter
from core.converter import SchemeConverter


class ConverterRegistry:
    """Registry for managing data converters."""

    def __init__(self):
        self._converters: Dict[str, DataConverter] = {}

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

    @staticmethod
    def create_default_registry():
        registry = ConverterRegistry()

        registry.register(
            "json",
            JSONConverter()
        )

        registry.register(
            "APDL",
            APDLConverter()
        )

        registry.register(
            "Scheme",
            SchemeConverter()
        )

        return registry