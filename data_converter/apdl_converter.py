"""Ansys APDL parameter file converter.

Provides :class:`APDLConverter`, which renders a parameter dictionary
as APDL ``key=value`` lines, marking nesting levels with ``!`` prefixes
and appending ``![units]`` comments for unit-aware parameters.
"""
from typing import Dict, Any

from .base import DataConverter, is_parameter


class APDLConverter(DataConverter):
    """Converter for mytype format (key = value with dot notation)."""

    def convert(self, data: Dict[str, Any]) -> str:
        """Convert to mytype format string."""
        lines = []
        self._flatten_dict(data, lines)
        return "\n".join(lines) + "\n"

    def _flatten_dict(self, data: Dict[str, Any], lines: list, prefix: str = "!"):
        """Flatten nested dict and collect lines."""
        for key, value in data.items():

            if isinstance(value, dict):
                if is_parameter(value):
                    lines.append(f"{key}={value["value"]}{f" ![{value["units"]}]" if "units" in value else ""}")
                    continue

                lines.append(f"{prefix}{key}")
                self._flatten_dict(value, lines, prefix + "!")
            else:
                lines.append(f"{key}={value}")

    def get_extension(self) -> str:
        return "parm"
