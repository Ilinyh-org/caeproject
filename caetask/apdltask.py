import os
import shutil
import tempfile
from pathlib import Path
from subprocess import Popen

from caetask import CAETask, log_execution_time


class APDLTask(CAETask):
    TYPE = "apdl"
    SERIALIZABLE_FIELDS = (
        "additional_link_files",
        "additional_text_files",
        "additional_text_files_codes",
        "application_version",
        "copy_link_files",
        "cores",
        "database_size",
        "geometry_file",
        "memory_size",
        "name",
        "new_parameter_name",
        "new_parameter_value",
        "parameters_file",
        "results_directory",
        "results_file_name",
        "results_files_names",
        "input_file",
        "log_file_name",
        #"status",
    )

    def __init__(
            self,
            name: str = 'task',
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
        self._copy_link_files = False
        self._results_directory = self.base_path
        self._geometry_file = ''
        # self.__working_directory_path = os.path.abspath(os.curdir)
        self._temporary_directory = None
        self._application_version = "212"
        self._cores = '2'
        self._new_parameter_name = None
        self._new_parameter_value = None
        self._memory_size = '2048'
        self._database_size = '1024'
        self._status = None

    def to_dict(self):
        data = super().to_dict()

        data["type"] = self.TYPE

        data.update({
            "results_file_name": self._results_file_name,
            "results_files_names": self._results_files_names,
            "additional_text_files": self._additional_text_files,
            "additional_text_files_codes": self._additional_text_files_codes,
            "copy_link_files": self._copy_link_files,
            "geometry_file": self._geometry_file,
            "application_version": self._application_version,
            "cores": self._cores,
            "new_parameter_name": self._new_parameter_name,
            "new_parameter_value": self._new_parameter_value,
            "memory_size": self._memory_size,
            "database_size": self._database_size,
            "status": self._status,
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

    def __repr__(self):
        return self._name

    def __str__(self):
        output = super().__str__()
        if self._temporary_directory:
            output += 'temporary directory path: ' + self._temporary_directory + '\n'
        if self._geometry_file:
            output += 'geometry file: ' + self._geometry_file + '\n'
        if self._results_file_name:
            output += 'results file: ' + self._results_file_name + '\n'
        output += 'number of threads in the task: ' + str(self._cores) + '\n'
        if self._new_parameter_name is not None:
            if isinstance(self._new_parameter_name, list):
                output += 'additional parameter: ' + str(self._new_parameter_name) + '\n'
            elif isinstance(self._new_parameter_name, list):
                output += 'additional parameters: ' + '\n'
                for parameter_name, parameter_value in zip(self._new_parameter_name, self._new_parameter_value):
                    output += str(parameter_name) + ' ' + str(parameter_value)
                output += '\n'
        return output

    @log_execution_time()
    def solve(self, cleanup=True, delete=True):
        tempdir = tempfile.TemporaryDirectory(
            dir=self._temporary_directory,
            delete=delete
        )

        self.load_files()

        self._create_files_in_running_dir(tempdir)

        print("started ansys task run \"" +
              os.path.basename(self._input_file) + "\"" +
              " in temporary directory " +
              os.path.basename(tempdir.name))

        # build the list of commands and attributes for the run
        # the run uses an environment variable like ansys180_dir
        application = [f'"{str(Path('%ansys' + self._application_version + '_dir%') / 'bin' / 'winx64' / ('ansys' + self._application_version))}"',
                       '-b',
                       '-m', self._memory_size,
                       '-db', self._database_size,
                       '-dir', tempdir.name,
                       '-np', self._cores,
                       '-j', self._name,
                       '-i', self._input_file.name,
                       '-o', str(Path(tempdir.name) / self.log_file_name)]
        if self._geometry_file:
            application += ['-gtmfile', self._geometry_file]
        if self._results_file_name:
            application += ['-resfile', self._results_file_name]
        if self._parameters_file:
            application += ['-parfile', self._parameters_file.name]
        if self._new_parameter_name:  # no new parameters
            if type(self._new_parameter_name) == list:  # list of  new parameter
                for a, b in zip(self._new_parameter_name, self._new_parameter_value):
                    application.append('-' + a)
                    application.append(b)
            else:  # one new parameter
                application.append('-' + self._new_parameter_name)
                application.append(self._new_parameter_value)

        # create links to or copy additional non-text files
        self._organize_additional_link_files(tempdir)

        # create the process from the configured application
        self._process = Popen(' '.join(application), shell=True).wait()
        print("finished ansys task run " +
              self._name +
              " in temporary directory " +
              Path(tempdir.name).name)

        # move results into the results folder
        for file in self._results_files_names:
            try:
                shutil.copy2(Path(tempdir.name) / file, self._results_directory)
                print(
                    f"File {file} of ansys task {self._name} copied from "
                    f"{Path(tempdir.name).name} to {self._results_directory.name}")
            except OSError:
                print(f"File {file} not found for copying to {self._results_directory}")

        # move the log file into the results folder
        try:
            shutil.copy2(Path(tempdir.name) / self._log_file_name, self._results_directory)
            print(
                f"Log file {self._log_file_name} of ansys task {self._name} copied from "
                f"{Path(tempdir.name).name} to {self._results_directory.name}")
        except OSError:
            print(f"Log file {self._log_file_name} not found for copying to {self._results_directory}")

        if cleanup:
            tempdir.cleanup()
        return self

    @property
    def geometry_file(self):
        return self._geometry_file

    @geometry_file.setter
    def geometry_file(self, name):
        self._geometry_file = name

    @property
    def cores(self):
        return self._cores

    @cores.setter
    def cores(self, cores):
        self._cores = str(cores)

    @property
    def new_parameter_name(self):
        return self._new_parameter_name

    @new_parameter_name.setter
    def new_parameter_name(self, name):
        self._new_parameter_name = name

    @property
    def new_parameter_value(self):
        return self._new_parameter_value

    @new_parameter_value.setter
    def new_parameter_value(self, value):
        self._new_parameter_value = value

    @property
    def memory_size(self):
        return self._memory_size

    @memory_size.setter
    def memory_size(self, memory_size):
        self._memory_size = str(memory_size)

    @property
    def database_size(self):
        return self._database_size

    @database_size.setter
    def database_size(self, database_size):
        self._database_size = str(database_size)

    @property
    def status(self):
        return self._process.poll()
