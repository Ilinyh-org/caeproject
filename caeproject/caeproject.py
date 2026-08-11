import pandas as pd

from caecase import CAECase
from caetask import run_threads

from core.serialization import Serializable
from core.file_manager import FileManager
from pathlib import Path
from typing import List


class CAEProject(Serializable):
    CONFIG_DEFAULT_NAME = "project_config.json"
    DIR_DEFAULT_NAME = "project"

    def __init__(
            self,
            base_path: Path | None = None,
            name: str | None = None,
    ):
        super().__init__(base_path, name)

        self.cases: dict[str, CAECase] = {}

    @classmethod
    def create_name(cls):
        return cls.DIR_DEFAULT_NAME

    def create_case(
            self,
            name: str | None = None,
    ) -> CAECase:

        case = CAECase.create_new(self.path, name)

        self.add_case(case)

        return case

    def create_cases(
            self,
            rows,
            factory,
            max_workers: int = 1,
    ):
        cases = run_threads(
            factory,
            rows,
            max_workers=max_workers,
        )

        for case in cases:
            self.add_case(case)

        return cases

    def add_case(self, case: CAECase):
        if case.project is not None:
            raise ValueError("Case already belongs to a project")

        if case.name in self.cases:
            raise ValueError(f"Case '{case.name}' already exists")

        case._project = self

        self.cases.setdefault(case.name, case)

    def update_case(self, case: CAECase):
        case._project = self
        self.cases[case.name] = case

    def remove_case(self, name: str):
        self.cases.pop(name)

    def solve(self, max_workers: int = 2):
        for case in self.cases:
            case.solve()

    def discover_cases(self):
        disk_cases = {}
        for path in self.path.iterdir():
            if not CAECase.is_case_directory(path):
                continue

            case = CAECase.load_config(path)
            disk_cases.setdefault(case.name, case)

        for name, case in disk_cases.items():
            # Add and update
            if case.name in self.cases:
                self.update_case(case)
            else:
                self.add_case(case)

            # Remove
            for name in list(self.cases):
                if name not in disk_cases:
                    self.remove_case(name)

    def get_results(self) -> pd.DataFrame:
        dataframes = [
            case.get_results()
            for case in self.cases.values()
        ]

        if not dataframes:
            return pd.DataFrame()

        return pd.concat(dataframes, ignore_index=True)

    def to_dict(self):
        """Prepare data for serialization."""
        data = super().to_dict()

        data.update({
            "cases": list(self.cases.keys()),
            "base_path": str(self.base_path)
        })

        return data

    @classmethod
    def create_new(
            cls,
            base_path: Path | None = None,
            name: str | None = None,
    ):
        name = name  or cls.create_name()
        base_path = base_path or Path.cwd()

        project_path = FileManager.create_project_dir(
            base_path,
            name,
        )

        return cls(
            base_path=project_path.parent,
            name=project_path.name,
        )

    @classmethod
    def from_existing_dir(cls, path: Path):
        """Load project from an existing folder."""
        return cls(base_path=path.parent, name=path.name)
