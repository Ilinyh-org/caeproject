import os
import shutil
import fnmatch
import tempfile
from pathlib import Path
from subprocess import Popen

from caetask import CAETask, log_execution_time


class FluentTask(CAETask):
    TYPE = "fluent"
    SERIALIZABLE_FIELDS = (
        "additional_link_files",
        "additional_text_files",
        # "additional_text_files_codes",
        "application_version",
        "copy_link_files",
        "threads",
        "name",
        "results_directory",
        "input_file",
        "log_file_name",
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
        # self.__working_directory_path = os.path.abspath(os.curdir)
        self._temporary_directory = None
        self._application_version = "212"
        self._dimension = "2d"
        self._graphics_regime = 'g'
        self._threads = '4'

    def __repr__(self):
        return self.name

    def __str__(self):
        output = super().__str__()
        if self._temporary_directory:
            output += 'temporary directory path: ' + self._temporary_directory + '\n'
        if self._results_file_name:
            output += 'results file: ' + self._results_file_name + '\n'
        output += 'number of threads in the task: ' + str(self._threads) + '\n'
        return output

    @log_execution_time()
    def solve(self, cleanup=True):
        tempdir = tempfile.TemporaryDirectory(dir=self._temporary_directory)

        self.load_files()

        self._create_files_in_running_dir(tempdir)

        print("started Fluent task run \"" +
              self._input_file.name + "\"" +
              " in temporary directory " +
              tempdir.name)

        application = [f'"{str(Path('%AWP_ROOT' + self._application_version + '%') / 'fluent' / 'ntbin' / 'win64' / 'fluent.exe')}"',
                       self._dimension,
                       # '-r', self.__application_version[0:2] + '.' + self.__application_version[2:3] + '.0',
                       *(['-' + self._graphics_regime] if self._graphics_regime is not None else []),  # run without graphics
                       '-i', self._input_file.name]

        # create links to or copy additional non-text files
        self._organize_additional_link_files(tempdir)  #move above

        # create the process from the configured application
        with open(Path(tempdir.name) / self.log_file_name, 'w') as f:
            self._process = Popen(' '.join(application),
                                  shell=True,
                                  stdout=f,
                                  cwd=tempdir.name).wait()
        print("finished ansys task run " +
              self.name +
              " in temporary directory " +
              Path(tempdir.name).name)

        # check regular expressions and extend the file list accordingly
        results_files_names_to_add = []
        results_files_names_to_remove = []
        for file in self._results_files_names:
            if any(ch in file for ch in ['*', '?', '+']):
                try:
                    for f in os.listdir(tempdir.name):
                        if fnmatch.fnmatch(f, file):
                            results_files_names_to_add.append(f)
                    results_files_names_to_remove.append(file)
                except Exception:
                    pass
        self._results_files_names.extend(results_files_names_to_add)
        for file in results_files_names_to_remove:
            self._results_files_names.remove(file)

        # move results into the results folder
        for file in self._results_files_names:
            try:
                shutil.copy2(Path(tempdir.name) / file, self._results_directory)
                print(f"File {file} of fluent task {self.name} copied from "
                      f"{tempdir.name} to {self._results_directory.name}")
            except OSError:
                print(f"File {file} not found for copying to {self._results_directory}")

        # move the log file into the results folder
        try:
            shutil.copy2(Path(tempdir.name) / self._log_file_name, self._results_directory)
            print(
                f"Log file {self._log_file_name} of fluent task {self._name} copied from "
                f"{tempdir.name} to {self._results_directory.name}")
        except OSError:
            print(f"Log file {self._log_file_name} not found for copying to {self._results_directory}")

        if cleanup:
            tempdir.cleanup()
        return self

    @property
    def dimension(self):
        return self._dimension

    @dimension.setter
    def dimension(self, dimension):
        if dimension not in ["2d", "3d", "2ddp", "3ddp"]:
            raise ValueError("Unknown task dimension type: " + dimension)
        self._dimension = dimension

    @property
    def threads(self):
        return self._threads

    @threads.setter
    def threads(self, threads):
        self._threads = str(threads)


    def to_dict(self):
        data = super().to_dict()

        data["type"] = self.TYPE

        data.update({
            "results_file_name": self._results_file_name,
            "results_files_names": self._results_files_names,
            "additional_text_files": self._additional_text_files,
            "additional_text_files_codes": self._additional_text_files_codes,
            "copy_link_files": self._copy_link_files,
            "application_version": self._application_version,
            "dimension": self._dimension,
            "threads": self._threads,
        })

        #data.update({"paths": [self.serialize(p, relative_to=self.base_path) for p in self._additional_text_files]})

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
