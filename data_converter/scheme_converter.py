"""Indented scheme-format data converter.

Provides :class:`SchemeConverter`, which renders a parameter
dictionary as plain text with nested dictionaries indented by four
spaces (``key:`` headers, ``key = value`` leaves).
"""
from typing import Any

from .base import DataConverter


class SchemeConverter(DataConverter):
    """Converter for mytype format with indented sections."""

    def convert(self, data: dict[str, Any]) -> str:
        """Convert to mytype format with indentation."""
        lines = []
        self._dict_to_indented(data, lines)
        return "\n".join(lines)

    def _dict_to_indented(self, data: dict[str, Any], lines: list, indent: int = 0):
        """Convert dict to indented format."""
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{' ' * indent}{key}:")
                self._dict_to_indented(value, lines, indent + 4)
            else:
                lines.append(f"{' ' * indent}{key} = {value}")

    def get_extension(self) -> str:
        return "txt"
