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
        self._additional_text_files = []
        self._additional_text_files_codes = []
        self._additional_link_files = []
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
            "additional_link_files": self._additional_link_files,
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
                for parameter_name, parameter_value in zip(self._new_parameter_name, self._new_parameter_value):
                    output += str(parameter_name) + ' ' + str(parameter_value)
                output += '\n'
        return output

    def __organize_additional_link_files(self, tempdir):
        # добавление ссылок на дополнительные файлы
        for file in self._additional_link_files:
            src = file
            dst = Path(tempdir.name) / Path(file).name
            if self._copy_link_files:
                shutil.copy2(src, tempdir.name)
                continue
            try:  # создание символьной ссылки
                os.symlink(src, dst, target_is_directory=False, dir_fd=None)
            except OSError as e:
                if e.winerror == 1314:
                    print("Ошибка 1314: Недостаточно прав для создания символьной ссылки. \n"
                          "Рекомендуем включить Режим Разработчика. Сейчас будет создана жёсткая ссылка")
                    try:  # создание жёсткой ссылки
                        os.link(src, dst)
                    except OSError as e:
                        if e.winerror == 17:
                            raise OSError(
                                "Ошибка 1314: Не удалось создать жёсткую ссылку, т.к. файл на другом разделе.\n"
                                "Для прямого копирования файлов вместо создания ссылок, "
                                "укажите параметр copy_link_files=True в конструкторе\n")
                        else:
                            raise OSError(f"Произошла ошибка OSError: {e}")
                else:
                    raise OSError(f"Произошла ошибка OSError: {e}")

    @log_execution_time()
    def solve(self, cleanup=True, delete=True):
        tempdir = tempfile.TemporaryDirectory(dir=self._temporary_directory,
                                              delete=delete)

        self.load_inputs()

        # чтение исходных файлов и запись их в рабочей директории
        if self._parameters_file:
            with open(Path(tempdir.name) / self._parameters_file.name, 'w') as f:
                f.writelines(self._parameters_file_code)
        if self._input_file:
            with open(Path(tempdir.name) / self._input_file.name, 'w') as f:
                f.writelines(self._input_file_code)
        for file in self._additional_text_files:
            with open(Path(tempdir.name) / file[0], 'w') as f:
                f.writelines(file[1])

        print("запущен расчёт ансис задачи \"" +
              os.path.basename(self._input_file) + "\"" +
              " во временной директории " +
              os.path.basename(tempdir.name))

        # составляем список команд и аттрибутов для запуска
        # для запуска используется переменная среды типа ansys180_dir
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

        # создание ссылок или копирование дополнительных нетекстовых файлов
        self.__organize_additional_link_files(tempdir)

        # создание процесса по сконфигурированному application
        self._process = Popen(' '.join(application), shell=True).wait()
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
            print(f"Файл лога {self._log_file_name} не найден для копирования в {self._results_directory}")

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
