# caeproject/__init__.py
"""Top-level CAE project package.

Exposes :class:`~caeproject.caeproject.CAEProject`, which groups
parameter sets and CAE tasks into a single runnable project.
"""
from .caeproject import CAEProject

__all__ = ['CAEProject']
