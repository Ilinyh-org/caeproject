
import caetask
from core.node import Node
from pathlib import Path
from core.file_manager import FileManager
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

    # In your main class
    def parameters_save(self,
                        format_type: str = 'json',
                        filename: str = None,
                        **filter_kwargs):
        """Save parameters with optional filtering and format.

        Args:
            format_type: Output format - 'json', 'mytype', or 'mytype_indented'
            **filter_kwargs: Filters to pass to to_dict() (include/exclude)
        """
        parameters = self.parameters
        if filter_kwargs.get('new_system'):
            parameters.to_units_system(**filter_kwargs)
        data = parameters.to_dict(**filter_kwargs)
        self.file_manager.save_immediately(data, format_type=format_type, filename=filename)

    @property
    def files(self) -> List[str]:
        return self.file_manager.files

    @files.setter
    def files(self, files):
        self.file_manager._files = files

    @property
    def path(self) -> Path:
        return self.file_manager.case_dir
