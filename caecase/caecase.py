
import caetask

from caecase.utils import is_case_dir_name
from core.node import Node
from pathlib import Path
from caecase.file_manager import FileManager
from core.serialization import Serializable
from typing import List, Iterable


class CAECase(Serializable):
    CONFIG_DEFAULT_NAME = "case_config.json"

    def __init__(self,
                 base_path: Path = None,
                 case_path: Path = None):
        self.parameters = Node()
        self.tasks: List[caetask] = []
        self.status = {}

        self.base_path = base_path or Path.cwd()
        self.file_manager = FileManager(base_path)
        self.case_path = case_path or self.file_manager.create_case_dir(self.base_path)

    def add_files_to_case(self, files):
        """Delegates to FileManager."""
        if not isinstance(files, Iterable):
            files = [files]
        self.file_manager.add_files(files, self.case_path)

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

    @classmethod
    def from_dict(cls, data: dict, **kwargs):
        obj = cls(**kwargs)

        obj.parameters.from_dict(data.get("parameters", {}))
        obj.status = data.get("status", {})
        obj.files = data.get("files", [])

        return obj

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
        self.file_manager.save_immediately(data,
                                           self.case_path,
                                           format_type=format_type,
                                           filename=filename)

    @property
    def files(self) -> List[str]:
        return self.file_manager.files

    @files.setter
    def files(self, files):
        self.file_manager._files = files

    @property
    def path(self) -> Path:
        return self.case_path

    @classmethod
    def is_case_directory(cls, path: Path) -> bool:
        if not path.is_dir():
            return False

        if not is_case_dir_name(path.name):
            return False

        config_path = path / cls.CONFIG_DEFAULT_NAME

        return config_path.exists()