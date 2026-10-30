from pathlib import Path

from caetask import CAETask, log_execution_time
from subprocess import Popen

import shutil
from importlib.resources import files

class CFDPostTask(CAETask):
    TYPE = "cfdpost"
    SERIALIZABLE_FIELDS = (
        "additional_link_files",
        "application_version",
        "name",
        "results_files_names",
        "input_file",
        "log_file_name",
    )

    def __init__(
            self,
            name='task',
            base_path: Path | None = None,
            input_file: Path | str | None = None,
            parameters_file: Path | str | None = None,
            results_files_names: list[str] | None = None
    ):
        super().__init__(
            name=name,
            base_path=base_path,
            input_file=input_file,
            parameters_file=parameters_file,
            results_files_names=results_files_names
        )
        self._working_directory = self.base_path
        self._results_directory = self.base_path
        self._application_version = "212"

    def __repr__(self):
        return self._name

    def __str__(self):
        output = super().__str__()
        output += 'working directory path: ' + str(self._working_directory) + '\n'
        if self._results_file_name:
            output += 'results (input) file: ' + self._results_file_name + '\n'
        return output

    def _create_files_in_running_dir(
            self,
            dst_path: Path | str | None):
        dst_path = super()._create_files_in_running_dir(dst_path)

        src = files("data") / "JsonConfig.pm"
        shutil.copy2(src, dst_path)

    @log_execution_time()
    def solve(self):
        self.load_files()

        self._create_files_in_running_dir(self._working_directory.absolute())

        print(f"started cfdpost task run {self._input_file.name}")
        # build the list of commands and attributes for the run
        application = [f'"{str(Path('%AWP_ROOT' + self._application_version + '%') / 'CFD-Post' / 'bin' / 'cfdpost.exe')}"',
                       '-batch', self._input_file.name]

        if self._results_file_name:
            application.append('-results')
            application.append(self._results_file_name)

        # create the process from the configured application
        with open(self._working_directory / self.log_file_name, 'w') as f:
            self._process = Popen(' '.join(application),
                                  shell=True,
                                  stdout=f,
                                  cwd=self._working_directory).wait()
        print(f"finished processing results {self._input_file.name}")

    def to_dict(self):
        data = super().to_dict()

        data["type"] = self.TYPE

        data.update({
            "results_files_names": self._results_files_names,
            "application_version": self._application_version,
            "working_directory": str(self._working_directory),
        })

        data["parameters_file"] = self.serialize(
            self._parameters_file,
            relative_to=self.base_path,
        )

        data["input_file"] = self.serialize(
            self._input_file,
            relative_to=self.base_path,
        )

        data["results_directory"] = self.serialize(
            self._results_directory,
            relative_to=self.base_path,
        )

        return data