import json
from pathlib import Path
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


class JSONConverter(DataConverter):
    """Converter for JSON format."""

    def convert(self, data: Dict[str, Any]) -> str:
        """Convert to JSON string."""
        return json.dumps(data, indent=4, ensure_ascii=False)

    def get_extension(self) -> str:
        return "json"


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


class SchemeConverter(DataConverter):
    """Converter for mytype format with indented sections."""

    def convert(self, data: Dict[str, Any]) -> str:
        """Convert to mytype format with indentation."""
        lines = []
        self._dict_to_indented(data, lines)
        return "\n".join(lines)

    def _dict_to_indented(self, data: Dict[str, Any], lines: list, indent: int = 0):
        """Convert dict to indented format."""
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{' ' * indent}{key}:")
                self._dict_to_indented(value, lines, indent + 4)
            else:
                lines.append(f"{' ' * indent}{key} = {value}")

    def get_extension(self) -> str:
        return "txt"


def is_parameter(data: dict):
    return 'value' in data