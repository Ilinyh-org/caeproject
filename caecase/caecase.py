
import caetask
from caetask import CAETask

from caecase.utils import is_case_dir_name
from core.node import Node
from pathlib import Path
from core.file_manager import create_case_dir, add_files, save
from core.serialization import Serializable
from typing import List, Iterable
from core.serialization import serialize


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

        case_path = create_case_dir(base_path, name)

        return cls(
            base_path=case_path.parent,
            name=case_path.name,
        )

    def add_task(self, task: CAETask):
        if task.case is not None:
            raise ValueError(
                "Task already belongs to a vase"
            )
        task._case = self

        self.tasks.append(task)

    def create_task(
            self,
            task_class: CAETask,
            name: str,
    ) -> CAETask:

        task = task_class.create_new(name, self.path)
        task._case = self

        self.add_task(task)

        return task

    def remove_task(self, task):
        self.tasks.remove(task)

        task._case = None

    def create_name(self):
        return create_case_dir(self.base_path)

    def add_files_to_case(self, files):
        """Delegates to FileManager."""
        if not isinstance(files, Iterable):
            files = [files]
        self.files += add_files(files, self.path)

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
        data = super().to_dict()

        data.update({
            "parameters": self.parameters.to_dict(),
            "files": [serialize(file) for file in self.files],
            "tasks": [t.to_dict() for t in self.tasks],
            "status": self.status
        })

        return data

    @classmethod
    def from_dict(cls, data: dict, **kwargs):
        obj = cls(**kwargs)

        obj.parameters.from_dict(data.get("parameters", {}))
        obj.status = data.get("status", {})
        obj.files = [Path(file) for file in data.get("files", [])]

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

        save(
            data=data,
            path=self.path,
            format_type=format_type,
            filename=filename
        )

    def add_task(self, task: CAETask):
        self.tasks.append(task)

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