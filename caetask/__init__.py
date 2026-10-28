"""CAE task package.

Exposes the task base class :class:`~caetask.caetask.CAETask`, the
solver-specific tasks :class:`~caetask.apdltask.APDLTask`,
:class:`~caetask.fluenttask.FluentTask`, and
:class:`~caetask.cfdposttask.CFDPostTask`, plus helpers for running
multiple tasks concurrently.
"""

from .apdltask import APDLTask
from .caetask import CAETask, log_execution_time
from .cfdposttask import CFDPostTask
from .fluenttask import FluentTask
from .solvers import run_processes, run_threads

__all__ = ['CAETask',
           'log_execution_time',
           'APDLTask',
           'FluentTask',
           'CFDPostTask',
           'run_processes',
           'run_threads',]
