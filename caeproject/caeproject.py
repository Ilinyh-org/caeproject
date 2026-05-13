
from caecase import CAECase

from core.serialization import Serializable
from pathlib import Path
from typing import List


CONFIG_DEFAULT_NAME = "project_config.json"

class CAEProject(Serializable):
    def __init__(self, base_path: Path = None):
        if base_path is None:
            self.base_path = Path.cwd()
        else:
            self.base_path = base_path

        self.cases: List[CAECase] = []


    def discover_cases(self):
        self.cases = []

        for path in self.base_path.iterdir():
            if CAECase.is_case_directory(path):
                case = CAECase.load_config(path)

                case.base_path = path

                self.cases.append(case)
