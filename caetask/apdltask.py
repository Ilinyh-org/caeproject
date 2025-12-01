import os
import shutil
import tempfile
from subprocess import Popen

from caetask.caetask import CAETask, log_execution_time


class APDLTask(CAETask):
    def __init__(self, task_name='task'):
        super().__init__(task_name)
        self._task_name = task_name
        self._input_file = ''
        self._input_file_code = ''
        self._log_file = task_name + '.log'
        self._parameters_file_name = ''
        self._parameters_file_code = ''
        self._results_file_name = ''
        self._results_files_names = []
        self._additional_text_files = []
        self._additional_text_files_codes = []
        self._additional_link_files = []
        self._copy_link_files = False
        self.__results_dir_path = os.path.abspath(os.curdir)
        self._geometry_file_name = ''
        # self.__working_directory_path = os.path.abspath(os.curdir)
        self._temporary_directory_path = None
        self._application_version = "212"
        self._cores = '2'
        self._new_parameter_name = None
        self._new_parameter_value = None
        self._process_type = 'serial'
        self._memory_size = '2048'
        self._database_size = '1024'
        self._process = None
        self._status = None

    def __repr__(self):
        return self._task_name

    def __str__(self):
        output = super().__str__()
        if self._temporary_directory_path:
            output += 'путь временной директории: ' + self._temporary_directory_path + '\n'
        if self._geometry_file_name:
            output += 'файл геометрии: ' + self._geometry_file_name + '\n'
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
            dst = os.path.join(tempdir.name, os.path.basename(file))
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
        tempdir = tempfile.TemporaryDirectory(dir=self._temporary_directory_path,
                                              delete=delete)

        # чтение исходных файлов и запись их в рабочей директории
        if self._parameters_file_name:
            with open(os.path.join(tempdir.name, os.path.basename(self._parameters_file_name)), 'w') as f:
                f.writelines(self._parameters_file_code)
        if self._input_file:
            with open(os.path.join(tempdir.name, os.path.basename(self._input_file)), 'w') as f:
                f.writelines(self._input_file_code)

        for file in self._additional_text_files:
            with open(os.path.join(tempdir.name, os.path.basename(file[0])), 'w') as f:
                f.writelines(file[1])

        print("запущен расчёт ансис задачи \"" +
              os.path.basename(self._input_file) + "\"" +
              " во временной директории " +
              os.path.basename(tempdir.name))

        # составляем список команд и аттрибутов для запуска
        # для запуска используется переменная среды типа ansys180_dir
        application = [f'"{os.path.join('%ansys' + self._application_version + '_dir%',
                                        'bin',
                                        'winx64',
                                        'ansys' + self._application_version)}"',
                       '-b',
                       '-m', self._memory_size,
                       '-db', self._database_size,
                       '-dir', tempdir.name,
                       '-np', self._cores,
                       '-j', self._task_name,
                       '-i', os.path.basename(self._input_file),
                       '-o', os.path.join(tempdir.name, self._log_file),
                       '-gtmfile', self._geometry_file_name,
                       '-resfile', self._results_file_name,
                       '-parfile', os.path.basename(self._parameters_file_name)]
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
        if self._process_type == 'serial':
            # при создании процесса список application превращается в строку
            self._process = Popen(' '.join(application), shell=True).wait()
            print("закончен расчёт ансис задачи " +
                  self._task_name +
                  " во временной директории " +
                  os.path.basename(tempdir.name))
        elif self._process_type == 'parallel':
            # при создании процесса список application превращается в строку
            self._process = Popen(' '.join(application), shell=True)

        # переносим результаты в папку результатов
        for file in self._results_files_names:
            try:
                shutil.copy2(os.path.join(tempdir.name, file), self.__results_dir_path)
                print(
                    f"Файл {file} ансис задачи {self._task_name} скопирован из {os.path.basename(tempdir.name)} в {os.path.basename(self.__results_dir_path)}")
            except OSError:
                print(f"Файл {file} не найден для копирования в {self.__results_dir_path}")

        if cleanup:
            tempdir.cleanup()
        return self

    @property
    def geometry_file_name(self):
        return self._geometry_file_name

    @geometry_file_name.setter
    def geometry_file_name(self, name):
        self._geometry_file_name = name

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
    def process_type(self):
        return self._process_type

    @process_type.setter
    def process_type(self, value):
        if value in ['serial', 'parallel']:
            self._process_type = value
        else:
            raise ValueError

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
