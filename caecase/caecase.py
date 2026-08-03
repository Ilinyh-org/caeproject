import pandas as pd

import data_converter
from caetask import CAETask
from caetask.default_registry import create_default_task_registry

from .utils import is_case_dir_name
from core.node import Node
from pathlib import Path
from core.file_manager import create_case_dir, add_files, save
from core.serialization import Serializable
from typing import List, Iterable


def append_df(df_main: pd.DataFrame, df_new: pd.DataFrame):
    if df_new is None or df_new.empty:
        return df_main
    if df_main.empty:
        return df_new
    return pd.concat([df_main, df_new])


def get_csv_results(file: Path | str):

    df = pd.read_csv(file)

    return df


class CAECase(Serializable):
    CONFIG_DEFAULT_NAME = "case_config.json"

    def __init__(
            self,
            base_path: Path | None = None,
            name: str | None = None,
    ):
        super().__init__(base_path, name)

        self._project = None

        self._files = []
        self.parameters = Node()
        self.tasks: List[CAETask] = []
        self.status = {}

    @classmethod
    def create_new(
            cls,
            base_path: Path | str | None = None,
            name: str | None = None,
    ):
        base_path = cls.normalize_path(base_path)

        case_path = create_case_dir(base_path, name)

        return cls(
            base_path=case_path.parent,
            name=case_path.name,
        )

    def add_task(self, task: CAETask):
        if task.case is not None:
            raise ValueError(
                "Task already belongs to a case"
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

    def get_results(self):
        df = pd.DataFrame()
        for task in self.tasks:
            for file in task.results_files_names:
                # проверка типа файла
                if file.name.suffix() == "csv":
                    df_file = get_csv_results(file)
                    df_file["ID"] = self.name
                    df = append_df(df, df_file)
                if file.name.suffix() == "dat":
                    pass
                if file.name.suffix() == "json":
                    pass

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
        data ={
            "parameters": self.parameters.to_dict(),
            "files": [self.serialize(file) for file in self.files],
            "tasks": [t.to_dict() for t in self.tasks],
            "status": self.status
        }

        return data

    @classmethod
    def from_dict(
            cls,
            data: dict,
            *,
            base_path: Path | str | None = None,
            name: str | None = None
    ):
        base_path = cls.normalize_path(base_path)

        obj = cls(base_path=base_path, name=name)

        obj.parameters.from_dict(data.get("parameters", {}))
        obj.status = data.get("status", {})
        obj.files = [Path(file) for file in data.get("files", [])]

        obj.tasks = []
        registry = create_default_task_registry()
        for task_data in data.get("tasks", []):
            task_type = registry.get(task_data["type"])
            obj.tasks.append(
                task_type.from_dict(
                    task_data,
                    base_path=obj.path
                )
            )

        return obj

    def parameters_save(self,
                        format_type: str = 'json',
                        filename: str = None,
                        **filter_kwargs):
        """Save parameters with optional filtering and format.

        Args:
            format_type: Output format - 'json', 'mytype', or 'mytype_indented'
            filename: File name
            **filter_kwargs: Filters to pass to to_dict() (include/exclude)
        """
        parameters = self.parameters
        if filter_kwargs.get('new_system'):
            parameters.to_units_system(**filter_kwargs)
        data = parameters.to_dict(**filter_kwargs)

        registry = data_converter.create_default_converter_registry()
        converter = registry.get(format_type)
        data = converter.convert(data)

        if not filename:
            filename = "case_data"
        if filename.find(".") == -1:
            filename += "." + converter.get_extension()

        save(
            data=data,
            path=self.path,
            filename=filename
        )

    def add_task(self, task: CAETask):
        self.tasks.append(task)

    @property
    def project(self):
        return self._project

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