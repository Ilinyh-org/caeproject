from pathlib import Path
from collections.abc import Callable, Iterable

from caecase import CAECase
from caeproject import CAEProject
from caetask.apdltask import APDLTask


class APDLWorkflow:
    def __init__(
            self,
            project: CAEProject,
            apdl_file: Path | str,
            task_name: str,
            configure_case: Callable[[CAECase, dict], None],
    ):
        self.project = project
        self.apdl_file = Path(apdl_file)
        self.task_name = task_name
        self.configure_case = configure_case

    def create_case(self, row: dict) -> CAECase:
        case = CAECase.create_new(self.project.path)

        self.configure_case(case, row)

        case.add_files_to_case([self.apdl_file])

        parameters_filename = f"{self.task_name}.parm"

        case.parameters_save(
            filename=parameters_filename,
            format_type="APDL",
            new_system="SI",
        )

        case.create_task(
            APDLTask,
            self.task_name,
            input_file=f"{self.task_name}.inp",
            parameters_file=parameters_filename,
            log_file_name=f"log_{self.task_name}.log",
            results_files_names=["RESULTS.csv"],
        )

        case.save_config()

        return case

    def create_cases(
            self,
            rows: Iterable[dict],
            max_workers: int = 1,
    ):
        return self.project.create_cases(
            rows,
            self.create_case,
            max_workers=max_workers,
        )