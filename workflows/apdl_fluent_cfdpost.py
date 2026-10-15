from pathlib import Path
from collections.abc import Callable, Iterable

from caecase import CAECase
from caeproject import CAEProject
from caetask.apdltask import APDLTask
from caetask.fluenttask import FluentTask
from caetask.cfdposttask import CFDPostTask
from tests.integration.test_caetask.test_apdltask import apdl_file
from tests.integration.test_caetask.test_cfdposttask import cse_cfdpost_file


class APDLFluentCFDPostWorkflow:
    def __init__(
        self,
        project: CAEProject,
        apdl_file: Path | str,
        fluent_file: Path | str,
        cfdpost_file: Path | str,
        task_name: str,
        configure_case: Callable[[CAECase, dict], None],
    ):
        self.project = project
        self.apdl_file = Path(apdl_file)
        self.fluent_file = Path(fluent_file)
        self.cfdpost_file = Path(cfdpost_file)
        self.task_name = task_name
        self.configure_case = configure_case

    def create_case(self, row: dict) -> CAECase:
        case = CAECase.create_new(self.project.path)

        self.configure_case(case, row)

        case.add_files_to_case([
            self.apdl_file,
            self.fluent_file,
            self.cfdpost_file,
        ])

        parameters_filename = self.task_name

        apdl_parameters_filename = case.parameters_save(
            filename=parameters_filename,
            format_type="APDL",
            new_system="SI",
        )

        json_parameters_filename = case.parameters_save(
            filename=parameters_filename,
            format_type="json",
            new_system="SI",
        )

        case.create_task(
            APDLTask,
            f"{self.task_name}_apdl",
            input_file=self.apdl_file.name,
            parameters_file=apdl_parameters_filename,
            log_file_name=f"log_{self.task_name}_apdl.log",
            results_files_names=["mesh.cdb"],
        )

        case.create_task(
            FluentTask,
            f"{self.task_name}_fluent",
            input_file=self.fluent_file.name,
            additional_link_files = [case.path / 'mesh.cdb'],
            log_file_name=f"log_{self.task_name}_fluent.log",
            results_files_names = ["results.cas.h5",
                                   "results.dat.h5"]
        )

        case.create_task(
            CFDPostTask,
            f"{self.task_name}_cfdpost",
            input_file=self.cfdpost_file.name,
            parameters_file=json_parameters_filename,
            log_file_name=f"log_{self.task_name}_cfdpost.log",
            results_files_names=["RESULTS.csv", "RESULTS_VELOCITY.csv"],
            working_directory = case.path,
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
