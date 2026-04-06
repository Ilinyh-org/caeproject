
import caetask
from .node import Node
from pathlib import Path
from .file_manager import FileManager
from typing import List, Iterable


class CAECase:
    def __init__(self, base_path: Path = None):
        self.parameters = Node()
        if base_path is None:
            base_path = Path.cwd()
        self.file_manager = FileManager(base_path)  # Handles dir creation and saving
        self.tasks: List[caetask] = []
        self.status = {}
        self._files = []

    def add_files_to_case(self, files):
        """Delegates to FileManager."""
        if not isinstance(files, Iterable):
            files = [files]
        self.file_manager.add_files(files)

    def solve(self):
        for task in self.tasks:
            task.solve()

    def save(self):
        """Public method to trigger a save."""
        self.file_manager.save_immediately(self.to_dict())

    def _notify_change(self):
        """
        Internal method called when state changes.
        Triggers the debounced save.
        """
        self.file_manager.schedule_save(self.to_dict())

    def to_dict(self):
        """Prepare data for serialization."""
        return {
            "parameters": self.parameters.to_dict(),
            "files": self.file_manager.files,  # Access list directly
            "tasks": [t.name for t in self.tasks], # Assuming tasks have names
            "status": self.status
        }

    def from_dict(self, data):
        """Restore state from dictionary."""
        self.parameters.from_dict(data.get("parameters", {}))
        self.file_manager.files = data.get("files", [])
        # Reconstruct tasks logic would go here
        self.status = data.get("status", {})

    def parameters_save(self):
        self.file_manager.save_immediately(self.parameters.to_dict())

    @property
    def files(self) -> List[str]:
        return self.file_manager.files

    @files.setter
    def files(self, files):
        self.file_manager._files = files

    @property
    def path(self) -> Path:
        return self.file_manager.case_dir
