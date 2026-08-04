
from caecase import CAECase

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

        self.cases: List[CAECase] = []

    @classmethod
    def create_name(cls):
        return cls.DIR_DEFAULT_NAME

    def create_case(
            self,
            name: str | None = None,
    ) -> CAECase:

        case = CAECase.create_new(self.path, name)
        case._project = self

        self.add_case(case)

        return case

    def add_case(self, case: CAECase):
        if case.project is not None:
            raise ValueError(
                "Case already belongs to a project"
            )
        case._project = self

        self.cases.append(case)

    def solve(self, max_workers: int = 2):
        for case in self.cases:
            case.solve()

    def discover_cases(self):
        for path in self.path.iterdir():
            if CAECase.is_case_directory(path):
                case = CAECase.load_config(path)

                if case not in self.cases:
                    self.cases.append(case)

    def to_dict(self):
        """Prepare data for serialization."""
        data = super().to_dict()

        data.update({
            "cases": [str(c.path) for c in self.cases],
            "base_path": str(self.base_path)
        })

        return data

    def add_case(self, new_case: CAECase):
        for case in self.cases:
            if case == new_case:
                return
        self.cases.append(new_case)

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
