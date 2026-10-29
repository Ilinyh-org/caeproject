"""JSON data converter.

Provides :class:`JSONConverter`, which serializes a parameter
dictionary to a pretty-printed JSON string.
"""
import json
from typing import Any

from .base import DataConverter


class JSONConverter(DataConverter):
    """Converter for JSON format."""

    def convert(self, data: dict[str, Any]) -> str:
        """Convert to JSON string."""
        return json.dumps(data, indent=4, ensure_ascii=False)

    def get_extension(self) -> str:
        return "json"
