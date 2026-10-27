"""Factory for the default CAE task registry."""
from . import CAETask
from .registry import TaskRegistry
from .apdltask import APDLTask
from .fluenttask import FluentTask
from .cfdposttask import CFDPostTask


def create_default_task_registry() -> TaskRegistry:
    """Create a task registry preloaded with the built-in task types.

    Registers the APDL, Fluent, and CFD-Post task classes under their
    lowercase type names ("apdl", "fluent", "cfdpost").
    """
    registry: TaskRegistry[str, CAETask] = TaskRegistry()

    registry.register("apdl", APDLTask)

    registry.register("fluent", FluentTask)

    registry.register("cfdpost", CFDPostTask)

    return registry