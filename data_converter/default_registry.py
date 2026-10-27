"""Factory for the default data converter registry."""

from .json_converter import JSONConverter
from .apdl_converter import APDLConverter
from .scheme_converter import SchemeConverter
from .registry import ConverterRegistry


def create_default_converter_registry():
    """Create a converter registry preloaded with the built-in formats.

    Registers JSON, APDL, and Scheme converter instances under the
    names "json", "APDL", and "Scheme".
    """
    registry = ConverterRegistry()

    registry.register("json", JSONConverter())

    registry.register("APDL", APDLConverter())

    registry.register("Scheme", SchemeConverter())

    return registry