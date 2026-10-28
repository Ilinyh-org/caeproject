"""ANSYS Mechanical APDL solver task.

Provides :class:`APDLTask`, a :class:`~caetask.caetask.CAETask` that
runs an APDL input file in batch mode from a temporary directory and
copies the results and log back into the results directory.
"""
import os
import shutil
import tempfile
from pathlib import Path
from subprocess import Popen

from caetask import CAETask, log_execution_time


class APDLTask(CAETask):
    """Task that runs an ANSYS Mechanical APDL calculation.

    Configures solver resources (cores, memory, database size),
    optional extra command-line parameters, and launches the APDL
    executable registered for the configured application version in
    batch mode.
    """

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
            output += 'путь временной директории: ' + self._temporary_directory + '\n'
        if self._geometry_file:
            output += 'файл геометрии: ' + self._geometry_file + '\n'
        if self._results_file_name:
            output += 'файл результатов: ' + self._results_file_name + '\n'
        output += 'количество потоков в задаче: ' + str(self._cores) + '\n'
        if self._new_parameter_name is not None:
            if isinstance(self._new_parameter_name, list):
                output += 'дополнительный параметр: ' + str(self._new_parameter_name) + '\n'
            elif isinstance(self._new_parameter_name, list):
                output += 'дополнительные параметры: ' + '\n'
                for parameter_name, parameter_value in zip(self._new_parameter_name,
                                                           self._new_parameter_value):
                    output += str(parameter_name) + ' ' + str(parameter_value)
                output += '\n'
        return output

    @log_execution_time()
    def solve(self, cleanup=True, delete=True):
        # pylint: disable=consider-using-with
        tempdir = tempfile.TemporaryDirectory(
            dir=self._temporary_directory,
            delete=delete
        )

        self.load_files()

        self._create_files_in_running_dir(tempdir)

        print("запущен расчёт ансис задачи \"" +
              os.path.basename(self._input_file) + "\"" +
              " во временной директории " +
              os.path.basename(tempdir.name))

        # составляем список команд и аттрибутов для запуска
        # для запуска используется переменная среды типа ansys180_dir
        application = [f'"{str(Path('%ansys' + self._application_version + '_dir%') / 'bin' / 'winx64' / ('ansys' + self._application_version))}"',  # pylint: disable=line-too-long
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

        # создание ссылок или копирование дополнительных нетекстовых файлов
        self._organize_additional_link_files(tempdir)

        # создание процесса по сконфигурированному application
        with Popen(' '.join(application), shell=True) as process:
            self._process = process.wait()
        print("закончен расчёт ансис задачи " +
              self._name +
              " во временной директории " +
              Path(tempdir.name).name)

        # переносим результаты в папку результатов
        for file in self._results_files_names:
            try:
                shutil.copy2(Path(tempdir.name) / file, self._results_directory)
                print(
                    f"Файл {file} ансис задачи {self._name} скопирован из "
                    f"{Path(tempdir.name).name} в {self._results_directory.name}")
            except OSError:
                print(f"Файл {file} не найден для копирования в {self._results_directory}")

        # переносим файл лога в папку результатов
        try:
            shutil.copy2(Path(tempdir.name) / self._log_file_name, self._results_directory)
            print(
                f"Файл лога {self._log_file_name} ансис задачи {self._name} скопирован из "
                f"{Path(tempdir.name).name} в {self._results_directory.name}")
        except OSError:
            print(f"Файл лога {self._log_file_name} не найден "
                  f"для копирования в {self._results_directory}")

        if cleanup:
            tempdir.cleanup()
        return self

    @property
    def geometry_file(self):
        """Path to the geometry (.gtm) file passed via ``-gtmfile``."""
        return self._geometry_file

    @geometry_file.setter
    def geometry_file(self, name):
        self._geometry_file = name

    @property
    def cores(self):
        """Number of CPU cores for the solver (stored as a string)."""
        return self._cores

    @cores.setter
    def cores(self, cores):
        self._cores = str(cores)

    @property
    def new_parameter_name(self):
        """Name (or list of names) of extra command-line parameter(s)."""
        return self._new_parameter_name

    @new_parameter_name.setter
    def new_parameter_name(self, name):
        self._new_parameter_name = name

    @property
    def new_parameter_value(self):
        """Value (or list of values) matching ``new_parameter_name``."""
        return self._new_parameter_value

    @new_parameter_value.setter
    def new_parameter_value(self, value):
        self._new_parameter_value = value

    @property
    def memory_size(self):
        """Total solver workspace memory in MB (stored as a string)."""
        return self._memory_size

    @memory_size.setter
    def memory_size(self, memory_size):
        self._memory_size = str(memory_size)

    @property
    def database_size(self):
        """Solver database memory in MB (stored as a string)."""
        return self._database_size

    @database_size.setter
    def database_size(self, database_size):
        self._database_size = str(database_size)

    @property
    def status(self):
        """Solver process status: ``None`` while running, else the exit code."""
        return self._process.poll()
