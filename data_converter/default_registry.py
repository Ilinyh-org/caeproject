
from .json_converter import JSONConverter
from .apdl_converter import APDLConverter
from .scheme_converter import SchemeConverter
from .registry import ConverterRegistry


def create_default_registry():
    registry = ConverterRegistry()

    registry.register("json", JSONConverter())

    registry.register("APDL", APDLConverter())

    registry.register("Scheme", SchemeConverter())

    return registry