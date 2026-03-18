# caecase/__init__.py
from .caecase import CAECase
from .node import Node
from .parameter import Parameter
from .file_manager import FileManager  # Add this line

__all__ = ['CAECase', 'Node', 'Parameter', 'FileManager']
