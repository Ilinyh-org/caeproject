from . import CAETask
from .registry import TaskRegistry
from .apdltask import APDLTask
from .fluenttask import FluentTask
from .cfdposttask import CFDPostTask


def create_default_task_registry() -> TaskRegistry:
    registry: TaskRegistry[str, CAETask] = TaskRegistry()

    registry.register("apdl", APDLTask)

    registry.register("fluent", FluentTask)

    registry.register("cfdpost", CFDPostTask)

    return registry