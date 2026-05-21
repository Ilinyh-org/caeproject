
import caetask

from caecase.utils import is_case_dir_name
from core.node import Node
from pathlib import Path
from core.file_manager import FileManager
from core.serialization import Serializable
from typing import List, Iterable


class CAECase(Serializable):
    CONFIG_DEFAULT_NAME = "case_config.json"

    def __init__(
            self,
            base_path: Path | None = None,
            name: str | None = None,
    ):
        super().__init__(base_path, name)

        self._files = []
        self.parameters = Node()
        self.tasks: List[caetask] = []
        self.status = {}

    @classmethod
    def create_new(
            cls,
            base_path: Path | None = None,
            name: str | None = None,
    ):
        base_path = base_path or Path.cwd()

        if not isinstance(base_path, (str, Path)):
            raise TypeError(
                f"Expected path to be str or Path, got {type(base_path).__name__}"
            )

        case_path = FileManager.create_case_dir(base_path, name)

        return cls(
            base_path=case_path.parent,
            name=case_path.name,
        )

    def create_name(self):
        return FileManager.create_case_dir(self.base_path)

    def add_files_to_case(self, files):
        """Delegates to FileManager."""
        if not isinstance(files, Iterable):
            files = [files]
        self.files += FileManager.add_files(files, self.path)

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
            "files": self.files,  # Access list directly
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

        FileManager.save(
            data=data,
            path=self.path,
            format_type=format_type,
            filename=filename
        )

    @property
    def files(self) -> List[str]:
        return self._files

    @files.setter
    def files(self, files):
        self._files = files

    @classmethod
    def is_case_directory(cls, path: Path) -> bool:
        if not path.is_dir():
            return False

        if not is_case_dir_name(path.name):
            return False

        config_path = path / cls.CONFIG_DEFAULT_NAME

        return config_path.exists()