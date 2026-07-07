import json
from typing import Dict, Any

from .base import DataConverter


class JSONConverter(DataConverter):
    """Converter for JSON format."""

    def convert(self, data: Dict[str, Any]) -> str:
        """Convert to JSON string."""
        return json.dumps(data, indent=4, ensure_ascii=False)

    def get_extension(self) -> str:
        return "json"
