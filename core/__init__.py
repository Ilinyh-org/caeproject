# core/__init__.py
"""Core building blocks of the CAE framework.

Groups the node tree (:mod:`core.node`), the unit-aware parameter
type (:mod:`core.parameter`), and the pandas series cross-merge
helper (:mod:`core.series_merger`).
"""

__all__ = ['node', 'parameter', 'series_merger']

from core import node, parameter, series_merger