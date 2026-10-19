import pandas as pd
from enum import Enum
import data_converter
from caetask import CAETask
from caetask.default_registry import create_default_task_registry

from .utils import is_case_dir_name
from core.node import Node
from pathlib import Path
from core.file_manager import create_case_dir, add_files, save
from core.serialization import Serializable
from typing import List, Iterable

import io, re

def append_df(df_main: pd.DataFrame, df_new: pd.DataFrame):
    if df_new is None or df_new.empty:
        return df_main
    if df_main.empty:
        return df_new
    return pd.concat([df_main, df_new])


def get_csv_results(file: Path | str) -> pd.DataFrame:
    text = Path(file).read_text()

    lines = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s or s.startswith("#") or re.match(r"^\[.*\]$", s):
            continue
        lines.append(s)

    # Find the first line that is purely numeric(-ish) → start of data
    first_data = next((i for i, ln in enumerate(lines)
                       if all(_is_num(p) for p in re.split(r"[,\s]+", ln))), len(lines))

    # Last text line before the data = column name (if any)
    header_lines = lines[:first_data]
    name = header_lines[-1] if header_lines else None
    data_lines = lines[first_data:]

    if not data_lines:
        return pd.DataFrame()

    # Try to see if the header is actually a real CSV header (multi-col names)
    # e.g. "U,V,W" -> all tokens non-numeric
    header_is_csv = (
        name is not None
        and "," in name
        and not any(_is_num(tok) for tok in name.split(","))
    )

    if header_is_csv:
        buf = io.StringIO(name + "\n" + "\n".join(data_lines))
        return pd.read_csv(buf)

    # Otherwise: no CSV header, values only, optional single column name
    df = pd.read_csv(io.StringIO("\n".join(data_lines)), header=None)
    if name is not None and df.shape[1] == 1:
        df.columns = [name]
    return df


def _is_num(s: str) -> bool:
    try:
        float(s); return True
    except ValueError:
        return False


class CaseStatus(Enum):
    NEW = "NEW"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


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
        self.status = CaseStatus.NEW

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
            task_class: type[CAETask],
            name: str,
            **attributes,
    ) -> CAETask:

        task = task_class.create_new(name, self.path)

        self.add_task(task)

        for name, value in attributes.items():
            setattr(task, name, value)

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
            for file_name in task.results_files_names:
                # проверка типа файла
                suffix = Path(file_name).suffix
                if suffix == ".csv":
                    df_file = get_csv_results(self.path / file_name)
                    df_file["ID"] = self.name
                    df = append_df(df, df_file)
                if suffix == ".dat":
                    pass
                if suffix == ".json":
                    pass
        return df

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
            "status": self.status.value
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
        obj.status = CaseStatus(data.get("status", CaseStatus.NEW.value))
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
                        **filter_kwargs) -> str:
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

        return filename

    def save_config(self, directory: Path | None = None):
        for task in self.tasks:
            task.load_files()

        super().save_config()

    @property
    def needs_solving(self) -> bool:
        return self.status != CaseStatus.DONE

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

    def __eq__(self, other):
        if not isinstance(other, CAECase):
            return NotImplemented
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)