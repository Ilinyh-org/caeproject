"""Top-level CAE project container.

Provides :class:`CAEProject`, a :class:`~core.serialization.Serializable`
that owns a project directory with multiple
:class:`~caecase.caecase.CAECase` subdirectories, supporting case
creation and discovery, concurrent solving of pending cases, and
collection of per-case results into a single DataFrame.
"""
import pandas as pd

from caecase import CAECase
from caetask import run_threads

from core.serialization import Serializable
from core.file_manager import FileManager
from pathlib import Path
from typing import List


class CAEProject(Serializable):
    """A project grouping multiple CAE cases in one directory.

    The project directory is ``base_path/name``; each case lives in
    its own subdirectory. Cases can be created, discovered from disk,
    registered or removed, solved concurrently, and their results
    collected together.
    """

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
        """Return the default project directory name."""
        return cls.DIR_DEFAULT_NAME

    def create_case(
            self,
            name: str | None = None,
    ) -> CAECase:
        """Create a new case inside the project directory and register it."""

        case = CAECase.create_new(self.path, name)

        self.add_case(case)

        return case

    def create_cases(
            self,
            rows,
            factory,
            max_workers: int = 1,
    ):
        """Create cases from parameter rows, at most ``max_workers`` in parallel.

        ``factory(case_config_row)`` must build and return a configured
        :class:`~caecase.caecase.CAECase`. All created cases are
        registered and returned in completion order.
        """
        cases = run_threads(
            factory,
            rows,
            max_workers=max_workers,
        )

        for case in cases:
            self.add_case(case)

        return cases

    def add_case(self, case: CAECase):
        """Register a case in the project.

        Raises:
            ValueError: if the case already belongs to a project or a
                case with the same name is already registered.
        """
        if case.project is not None:
            raise ValueError("Case already belongs to a project")

        if case.name in self.cases:
            raise ValueError(f"Case '{case.name}' already exists")

        case._project = self

        self.cases.setdefault(case.name, case)

    def update_case(self, case: CAECase):
        """Replace the registered case of the same name, re-pointing it to this project."""
        case._project = self
        self.cases[case.name] = case

    def remove_case(self, name: str):
        """Unregister the named case (raises KeyError if absent)."""
        self.cases.pop(name)

    def solve(self, max_workers: int = 2):
        """Solve all cases with ``needs_solving``, up to ``max_workers`` in parallel."""
        cases = [
            case
            for case in self.cases.values()
            if case.needs_solving
        ]

        run_threads(
            CAECase.solve,
            cases,
            max_workers=max_workers,
        )

    def discover_cases(self):
        """Synchronize registered cases with the case directories on disk.

        Loads every case directory inside the project path: new cases
        are added, existing ones are replaced, and registered cases
        whose directory no longer exists are removed.
        """
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
        """Collect all case results into one DataFrame.

        Each case's parameters are cross-joined with its results
        table; the per-case frames are concatenated with a fresh
        index. Returns an empty DataFrame if there are no cases.
        """
        dataframes = []
        for case in self.cases.values():
            parameters = case.parameters.to_dataframe()
            results = case.get_results()

            parameters_results = parameters.merge(results, how="cross")

            dataframes.append(parameters_results)

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
        """Create a new project directory under ``base_path`` and return the project.

        Defaults to the working directory and the default project name.
        """
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
