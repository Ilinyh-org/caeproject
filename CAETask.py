import shutil
from abc import ABCMeta, abstractmethod
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor
from threading import Lock

lock = Lock()


def run_processes(task, data, max_workers=10):  # часть модуля CAETask
    executor = ProcessPoolExecutor(max_workers=max_workers)
    # for index in range(3):
    #     executor.submit(create_task(index))
    results = []
    for result in executor.map(task, data):
        with lock:
            results.append(result)
    return results


def run_threads(task, data, max_workers=5):  # часть модуля CAETask
    executor = ThreadPoolExecutor(max_workers=max_workers)
    results = []
    for result in executor.map(task, data):
        with lock:
            results.append(result)
    return results


class CAETask:
    __metaclass__ = ABCMeta

    @abstractmethod
    def solve(self):
        ...

    @property
    @abstractmethod
    def input_file(self):
        ...

    @input_file.setter
    @abstractmethod
    def input_file(self, file):
        ...

    @property
    @abstractmethod
    def log_file_name(self):
        ...

    @log_file_name.setter
    @abstractmethod
    def log_file_name(self, name):
        ...

    @property
    @abstractmethod
    def parameters_file(self):
        ...

    @parameters_file.setter
    @abstractmethod
    def parameters_file(self, name):
        ...

    @property
    @abstractmethod
    def results_file_name(self):
        ...

    @results_file_name.setter
    @abstractmethod
    def results_file_name(self, name):
        ...

    @property
    @abstractmethod
    def geometry_file_name(self):
        ...

    @geometry_file_name.setter
    @abstractmethod
    def geometry_file_name(self, name):
        ...

    @property
    @abstractmethod
    def application_version(self):
        ...

    @application_version.setter
    @abstractmethod
    def application_version(self, name):
        ...

    @property
    @abstractmethod
    def working_directory_path(self):
        ...

    @working_directory_path.setter
    @abstractmethod
    def working_directory_path(self, name):
        ...


class APDLTask(CAETask):
    def __init__(self, task_name='task'):
        self.__task_name = task_name
        self.__input_file = ''
        self.__input_file_code = ''
        self.__log_file = task_name + '.log'
        self.__parameters_file = ''
        self.__parameters_file_code = ''
        self.__results_file_name = ''
        self.__results_files_names = []
        self.__additional_files = []
        self.__additional_files_codes = []
        self.__results_dir_path = './'
        self.__geometry_file_name = ''
        self.__working_directory_path = './'
        self.__application_version = "212"
        self.__cores = '2'
        self.__new_parameter_name = None
        self.__new_parameter_value = None
        self.__process_type = 'serial'
        self.__process = None
        self.__status = None

    def __repr__(self):
        return self.__task_name

    def __str__(self):
        output = ''
        output += 'имя задачи: ' + self.__task_name + '\n'
        output += 'исполняемый файл: ' + self.__input_file + '\n'
        output += 'файл логов: ' + self.__log_file + '\n'
        output += 'файл параметров: ' + self.__parameters_file + '\n'
        # output += 'путь временной директории: ' + self.__working_directory_path + '\n'
        # output += 'путь рабочей директории: ' + self.__working_directory_path + '\n'
        output += 'файл геометрии: ' + self.__geometry_file_name + '\n'
        # output += 'файл результатов: ' + self.__results_file_name + '\n'
        output += 'файл результатов: ' + self.__results_file_name + '\n'
        output += 'приложение: ' + self.__application_version + '\n'
        if self.__process_type == 'serial':
            output += 'задача создана в режиме очереди' + '\n'
        elif self.__process_type == 'parallel':
            output += 'задача создана в параллельном режиме' + '\n'
        output += 'количество потоков в задаче: ' + str(self.__cores) + '\n'
        if self.__new_parameter_name is not None:
            if isinstance(self.__new_parameter_name, list):
                output += 'дополнительный параметр: ' + str(self.__new_parameter_name) + '\n'
            elif isinstance(self.__new_parameter_name, list):
                output += 'дополнительные параметры: ' + '\n'
                for parameter_name, parameter_value in zip(self.__new_parameter_name, self.__new_parameter_value):
                    output += str(parameter_name) + ' ' + str(parameter_value)
                output += '\n'
        return output

    def solve(self):
        from subprocess import Popen

        tempdir = tempfile.TemporaryDirectory()
        # os.chdir(tempdir.name)

        if self.__parameters_file:
            with open(tempdir.name + "\\" + os.path.basename(self.__parameters_file), 'w') as f:
                f.writelines(self.__parameters_file_code)
        if self.__input_file:
            with open(tempdir.name + "\\" + os.path.basename(self.__input_file), 'w') as f:
                f.writelines(self.__input_file_code)

        for file in self.__additional_files:
            with open(tempdir.name + "\\" + os.path.basename(file[0]), 'w') as f:
                f.writelines(file[1])

        print("запущен расчёт ансис задачи \"" +
              os.path.basename(self.__input_file) + "\"" +
              " во временной директории " +
              os.path.basename(tempdir.name))

        # run mesh apdl script
        # составляем список команд и аттрибутов для запуска
        if self.__new_parameter_name is None:  # no new parameters
            # для запуска используется переменная среды типа ansys180_dir
            application = ['"%ansys' + self.__application_version
                           + '_dir%\\bin\\winx64\\'
                           + 'ansys' + self.__application_version + '"',
                           '-b',
                           '-dir', tempdir.name,
                           '-np', self.__cores,
                           '-j', self.__task_name,
                           '-i', os.path.basename(self.__input_file),
                           '-o', self.__log_file,
                           '-gtmfile', self.__geometry_file_name,
                           '-resfile', self.__results_file_name,
                           '-parfile', os.path.basename(self.__parameters_file)]
        else:  # new parameters exist
            application = ['"%ansys' + self.__application_version
                           + '_dir%\\bin\\winx64\\'
                           + self.__application_version + '"',
                           '-b',
                           '-dir', tempdir.name,
                           '-np', self.__cores,
                           '-j', self.__task_name,
                           '-i', os.path.basename(self.__input_file),
                           '-o', self.__log_file,
                           '-gtmfile', self.__geometry_file_name,
                           '-resfile', self.__results_file_name,
                           '-parfile', os.path.basename(self.__parameters_file)]
            if type(self.__new_parameter_name) == list:  # list of  new parameter
                for a, b in zip(self.__new_parameter_name, self.__new_parameter_value):
                    application.append('-' + a)
                    application.append(b)
            else:  # one new parameter
                application.append('-' + self.__new_parameter_name)
                application.append(self.__new_parameter_value)
        # создание процесса по сконфигурированному application
        if self.__process_type == 'serial':
            # при создании процесса список application превращается в строку
            self.__process = Popen(' '.join(application), shell=True).wait()
            print("закончен расчёт ансис задачи \"" +
                  os.path.basename(self.__input_file) + "\"" +
                  " во временной директории " +
                  os.path.basename(tempdir.name))
        elif self.__process_type == 'parallel':
            # при создании процесса список application превращается в строку
            self.__process = Popen(' '.join(application), shell=True)

        # переносим результаты в папку результатов
        for file in self.__results_files_names:
            try:
                shutil.copy2(tempdir.name + "\\" + file, self.__results_dir_path)
            except OSError as err:
                # print(f"Unexpected {err=}, {type(err)=}")
                print(f"Unexpected {err=}: " + tempdir.name + "\\" + file)

        tempdir.cleanup()
        return self

    # @CAETask.input_file_name
    @property
    def input_file(self):
        return self.__input_file

    # @CAETask.input_file_name.setter
    @input_file.setter
    def input_file(self, file):
        try:
            with open(file) as f:
                self.__input_file_code = f.readlines()
            self.__input_file = file
        except FileNotFoundError as err:
            print(f"Unexpected {err=}, {type(err)=}")
            raise

    @property
    def log_file(self):
        return self.__log_file

    @log_file.setter
    def log_file(self, file):
        self.__log_file = file

    @property
    def results_file_name(self):
        return self.__results_file_name

    @results_file_name.setter
    def results_file_name(self, name):
        self.__results_file_name = name

    @property
    def results_files_names(self):
        return self.__results_files_names

    @results_files_names.setter
    def results_files_names(self, flist):
        if type(flist) is list:
            self.__results_files_names = flist
        else:
            self.__results_files_names = [flist]

    @property
    def additional_files(self):
        return self.__additional_files

    @additional_files.setter
    def additional_files(self, flist):
        if type(flist) is not list:
            flist = [flist]
        for file in flist:
            try:
                with open(file) as f:
                    self.__additional_files.append((file, f.readlines()))
            except FileNotFoundError as err:
                print(f"Unexpected {err=}, {type(err)=}")
                raise

    @property
    def results_dir_path(self):
        return self.__results_dir_path

    @results_dir_path.setter
    def results_dir_path(self, path):
        self.__results_dir_path = os.path.abspath(path)
        
    @property
    def parameters_file(self):
        return self.__parameters_file

    @parameters_file.setter
    def parameters_file(self, file):
        try:
            with open(file) as f:
                self.__parameters_file_code = f.readlines()
            self.__parameters_file = file
        except FileNotFoundError as err:
            print(f"Unexpected {err=}, {type(err)=}")
            raise

    @property
    def geometry_file_name(self):
        return self.__geometry_file_name

    @geometry_file_name.setter
    def geometry_file_name(self, name):
        self.__geometry_file_name = name

    @property
    def application_version(self):
        return self.__application_version

    @application_version.setter
    def application_version(self, name):
        self.__application_version = name

    @property
    def working_directory_path(self):
        return self.__working_directory_path

    @working_directory_path.setter
    def working_directory_path(self, path):
        self.__working_directory_path = os.path.abspath(path)

    @property
    def cores(self):
        return self.__cores

    @cores.setter
    def cores(self, cores):
        self.__cores = str(cores)

    @property
    def new_parameter_name(self):
        return self.__new_parameter_name

    @new_parameter_name.setter
    def new_parameter_name(self, name):
        self.__new_parameter_name = name

    @property
    def new_parameter_value(self):
        return self.__new_parameter_value

    @new_parameter_value.setter
    def new_parameter_value(self, value):
        self.__new_parameter_value = value

    @property
    def process_type(self):
        return self.__process_type

    @process_type.setter
    def process_type(self, value):
        if value in ['serial', 'parallel']:
            self.__process_type = value
        else:
            raise ValueError

    @property
    def status(self):
        return self.__process.poll()


class FluentTask(CAETask):
    __counter = 0

    def __init__(self, task_name='task' + str(__counter)):
        self.__task_name = task_name
        self.__input_file = ''
        self.__log_file_name = task_name + '.log'
        self.__parameters_file_name = ''
        self.__results_file = ''
        self.__geometry_file_name = ''
        self.__working_directory_path = './'
        self.__application_version = "180"
        self.__dimension = "2d"
        self.__threads = '2'
        self.__new_parameter_name = None
        self.__new_parameter_value = None
        self.__process_type = 'serial'
        self.__process = None
        FluentTask.__counter += 1

    def __del__(self):
        FluentTask.__counter -= 1

    def __repr__(self):
        return self.__task_name

    def __str__(self):
        output = ''
        output += 'имя задачи: ' + self.__task_name + '\n'
        output += 'исполняемый файл: ' + self.__input_file + '\n'
        output += 'файл логов: ' + self.__log_file_name + '\n'
        output += 'файл параметров: ' + self.__parameters_file_name + '\n'
        output += 'путь рабочей директории: ' + self.__working_directory_path + '\n'
        output += 'файл геометрии: ' + self.__geometry_file_name + '\n'
        output += 'файл результатов: ' + self.__results_file_name + '\n'
        output += 'приложение: ' + self.__application_version + '\n'
        if self.__process_type == 'serial':
            output += 'задача создана в режиме очереди' + '\n'
        elif self.__process_type == 'parallel':
            output += 'задача создана в параллельном режиме' + '\n'
        output += 'количество потоков в задаче: ' + str(self.__threads) + '\n'
        if self.__new_parameter_name is not None:
            if isinstance(self.__new_parameter_name, list):
                output += 'дополнительный параметр: ' + str(self.__new_parameter_name) + '\n'
            elif isinstance(self.__new_parameter_name, list):
                output += 'дополнительные параметры: ' + '\n'
                for parameter_name, parameter_value in zip(self.__new_parameter_name, self.__new_parameter_value):
                    output += str(parameter_name) + ' ' + str(parameter_value)
                output += '\n'
        return output

    def solve(self):
        from subprocess import Popen
        import os
        if not os.path.isfile(self.__input_file):
            raise FileNotFoundError(self.__input_file)

        print("запущен расчёт fluent задачи \"" + self.__input_file + "\"")
        # составляем список команд и аттрибутов для запуска

        application = ['\"%AWP_ROOT' + self.__application_version
                       + '%\\fluent\\ntbin\\win64\\fluent.exe\"',
                       self.__dimension,
                        # '-r', self.__application_version[0:2] + '.' + self.__application_version[2:3] + '.0',
                       '-g',
                       '-i', self.__input_file]
                       # '-b', '-dir', self.__working_directory_path,
                       # '-np', self.__threads,
                       # '-j', self.__task_name,
                       # '-i', self.__input_file,
                       # '-o', self.__log_file_name + '.log',
                       # '-gtmfile', self.__geometry_file_name,
                       # '-resfile', self.__results_file_name,
                       # '-parfile', self.__parameters_file_name]

        # if self.__new_parameter_name is None:  # no new parameters
        #     # для запуска используется переменная среды типа AWP_ROOT202
        #     version_full = self.__application_version[:1] + '.' + self.__application_version[len(self.__application_version)]
        #     application = ['"%AWP_ROOT' + self.__application_version + '%\\fluent'
        #                    + '\\fluent' + self.__application_version + '\\'
        #                    + self.__application_version + '"',
        #                    '-b', '-dir', self.__working_directory_path,
        #                    '-np', self.__threads,
        #                    '-j', self.__task_name,
        #                    '-i', self.__input_file,
        #                    '-o', self.__log_file_name + '.log',
        #                    '-gtmfile', self.__geometry_file_name,
        #                    '-resfile', self.__results_file_name,
        #                    '-parfile', self.__parameters_file_name]
        # else:  # new parameters exist
        #     application = ['"%' + self.__application_version
        #                    + '_dir%\\bin\\winx64\\'
        #                    + self.__application_version + '"',
        #                    '-b', '-dir', self.__working_directory_path,
        #                    '-np', self.__threads,
        #                    '-j', self.__task_name,
        #                    '-i', self.__input_file,
        #                    '-o', self.__log_file_name + '.log',
        #                    '-gtmfile', self.__geometry_file_name,
        #                    '-resfile', self.__results_file_name,
        #                    '-parfile', self.__parameters_file_name]
        #     if type(self.__new_parameter_name) == list:  # list of  new parameter
        #         for a, b in zip(self.__new_parameter_name, self.__new_parameter_value):
        #             application.append('-' + a)
        #             application.append(b)
        #     else:  # one new parameter
        #         application.append('-' + self.__new_parameter_name)
        #         application.append(self.__new_parameter_value)
        # создание процесса по сконфигурированному application
        if self.__process_type == 'serial':
            # при создании процесса список application превращается в строку
            with open(self.__log_file_name + '.log', 'w') as f:
                self.__process = Popen(' '.join(application),
                                       shell=True,
                                       stdout=f,
                                       cwd=self.__working_directory_path).wait()
            print("закончен расчёт fluent задачи " + self.__input_file + "\"")
        elif self.__process_type == 'parallel':
            # при создании процесса список application превращается в строку
            self.__process = Popen(' '.join(application), shell=True)

    # @CAETask.input_file_name
    @property
    def input_file(self):
        return self.__input_file

    # @CAETask.input_file_name.setter
    @input_file.setter
    def input_file(self, file):
        self.__input_file = file

    @property
    def counter(self):
        return FluentTask.__counter

    @property
    def log_file_name(self):
        return self.__log_file_name

    @log_file_name.setter
    def log_file_name(self, name):
        self.__log_file_name = name

    @property
    def results_file_name(self):
        return self.__results_file_name

    @results_file_name.setter
    def results_file_name(self, name):
        self.__results_file_name = name

    @property
    def parameters_file(self):
        return self.__parameters_file

    @parameters_file.setter
    def parameters_file(self, file):
        self.__parameters_file = file

    @property
    def geometry_file_name(self):
        return self.__geometry_file_name

    @geometry_file_name.setter
    def geometry_file_name(self, name):
        self.__geometry_file_name = name

    @property
    def application_version(self):
        return self.__application_version

    @application_version.setter
    def application_version(self, name):
        self.__application_version = name

    @property
    def dimension(self):
        return self.__dimension

    @dimension.setter
    def dimension(self, dimension):
        if dimension not in ["2d", "3d", "2ddp", "3ddp"]:
            raise ValueError("Неизвестный тип размерности задачи: " + dimension)
        self.__dimension = dimension

    @property
    def working_directory_path(self):
        return self.__working_directory_path

    @working_directory_path.setter
    def working_directory_path(self, name):
        self.__working_directory_path = name

    @property
    def threads(self):
        return self.__threads

    @threads.setter
    def threads(self, threads):
        self.__threads = str(threads)

    @property
    def new_parameter_name(self):
        return self.__new_parameter_name

    @new_parameter_name.setter
    def new_parameter_name(self, name):
        self.__new_parameter_name = name

    @property
    def new_parameter_value(self):
        return self.__new_parameter_value

    @new_parameter_value.setter
    def new_parameter_value(self, value):
        self.__new_parameter_value = value


class CFDPostTask(CAETask):
    __counter = 0

    def __init__(self, task_name='task' + str(__counter)):
        self.__task_name = task_name
        self.__input_file = ''
        self.__log_file_name = task_name + '.log'
        self.__parameters_file_name = ''
        self.__results_file_name = ''
        self.__geometry_file_name = ''
        self.__working_directory_path = './'
        self.__application_version = "180"
        self.__dimension = "2d"
        self.__threads = '2'
        self.__new_parameter_name = None
        self.__new_parameter_value = None
        self.__process_type = 'serial'
        self.__process = None
        CFDPostTask.__counter += 1

    def __del__(self):
        CFDPostTask.__counter -= 1

    def __repr__(self):
        return self.__task_name

    def __str__(self):
        output = ''
        output += 'имя задачи: ' + self.__task_name + '\n'
        output += 'исполняемый файл: ' + self.__input_file + '\n'
        output += 'файл логов: ' + self.__log_file_name + '\n'
        output += 'файл параметров: ' + self.__parameters_file_name + '\n'
        output += 'путь рабочей директории: ' + self.__working_directory_path + '\n'
        output += 'файл геометрии: ' + self.__geometry_file_name + '\n'
        output += 'файл результатов: ' + self.__results_file_name + '\n'
        output += 'приложение: ' + self.__application_version + '\n'
        if self.__process_type == 'serial':
            output += 'задача создана в режиме очереди' + '\n'
        elif self.__process_type == 'parallel':
            output += 'задача создана в параллельном режиме' + '\n'
        output += 'количество потоков в задаче: ' + str(self.__threads) + '\n'
        if self.__new_parameter_name is not None:
            if isinstance(self.__new_parameter_name, list):
                output += 'дополнительный параметр: ' + str(self.__new_parameter_name) + '\n'
            elif isinstance(self.__new_parameter_name, list):
                output += 'дополнительные параметры: ' + '\n'
                for parameter_name, parameter_value in zip(self.__new_parameter_name, self.__new_parameter_value):
                    output += str(parameter_name) + ' ' + str(parameter_value)
                output += '\n'
        return output

    def solve(self):
        from subprocess import Popen
        import os
        if not os.path.isfile(self.__input_file):
            raise FileNotFoundError(self.__input_file)

        print("запущен расчёт fluent задачи \"" + self.__input_file + "\"")
        # составляем список команд и аттрибутов для запуска
        application = ['\"%AWP_ROOT' + self.__application_version
                       + '%\\fluent\\ntbin\\win64\\fluent.exe\"',
                       self.__dimension,
                        # '-r', self.__application_version[0:2] + '.' + self.__application_version[2:3] + '.0',
                       '-g',
                       '-i', self.__input_file]
                       # '-b', '-dir', self.__working_directory_path,
                       # '-np', self.__threads,
                       # '-j', self.__task_name,
                       # '-i', self.__input_file,
                       # '-o', self.__log_file_name + '.log',
                       # '-gtmfile', self.__geometry_file_name,
                       # '-resfile', self.__results_file_name,
                       # '-parfile', self.__parameters_file_name]

        # if self.__new_parameter_name is None:  # no new parameters
        #     # для запуска используется переменная среды типа AWP_ROOT202
        #     version_full = self.__application_version[:1] + '.' + self.__application_version[len(self.__application_version)]
        #     application = ['"%AWP_ROOT' + self.__application_version + '%\\fluent'
        #                    + '\\fluent' + self.__application_version + '\\'
        #                    + self.__application_version + '"',
        #                    '-b', '-dir', self.__working_directory_path,
        #                    '-np', self.__threads,
        #                    '-j', self.__task_name,
        #                    '-i', self.__input_file,
        #                    '-o', self.__log_file_name + '.log',
        #                    '-gtmfile', self.__geometry_file_name,
        #                    '-resfile', self.__results_file_name,
        #                    '-parfile', self.__parameters_file_name]
        # else:  # new parameters exist
        #     application = ['"%' + self.__application_version
        #                    + '_dir%\\bin\\winx64\\'
        #                    + self.__application_version + '"',
        #                    '-b', '-dir', self.__working_directory_path,
        #                    '-np', self.__threads,
        #                    '-j', self.__task_name,
        #                    '-i', self.__input_file,
        #                    '-o', self.__log_file_name + '.log',
        #                    '-gtmfile', self.__geometry_file_name,
        #                    '-resfile', self.__results_file_name,
        #                    '-parfile', self.__parameters_file_name]
        #     if type(self.__new_parameter_name) == list:  # list of  new parameter
        #         for a, b in zip(self.__new_parameter_name, self.__new_parameter_value):
        #             application.append('-' + a)
        #             application.append(b)
        #     else:  # one new parameter
        #         application.append('-' + self.__new_parameter_name)
        #         application.append(self.__new_parameter_value)
        # создание процесса по сконфигурированному application
        if self.__process_type == 'serial':
            # при создании процесса список application превращается в строку
            with open(self.__log_file_name + '.log', 'w') as f:
                self.__process = Popen(' '.join(application),
                                       shell=True,
                                       stdout=f,
                                       cwd=self.__working_directory_path).wait()
            print("закончен расчёт fluent задачи " + self.__input_file + "\"")
        elif self.__process_type == 'parallel':
            # при создании процесса список application превращается в строку
            self.__process = Popen(' '.join(application), shell=True)


class CFDPostTask(CAETask):
    __counter = 0

    def __init__(self, task_name='task' + str(__counter)):
        self.__task_name = task_name
        self.__input_file = ''
        self.__log_file_name = task_name + '.log'
        self.__parameters_file_name = ''
        self.__results_file_name = ''
        self.__report_file_name = task_name
        self.__working_directory_path = './'
        self.__application_version = "180"
        self.__threads = '2'
        self.__process_type = 'serial'
        self.__process = None
        CFDPostTask.__counter += 1

    def __del__(self):
        CFDPostTask.__counter -= 1

    def __repr__(self):
        return self.__task_name

    def __str__(self):
        output = ''
        output += 'имя задачи: ' + self.__task_name + '\n'
        output += 'исполняемый файл: ' + self.__input_file + '\n'
        output += 'файл логов: ' + self.__log_file_name + '\n'
        output += 'файл параметров: ' + self.__parameters_file_name + '\n'
        output += 'путь рабочей директории: ' + self.__working_directory_path + '\n'
        output += 'файл результатов (входных): ' + self.__results_file_name + '\n'
        output += 'файл результатов: ' + self.__results_file_name + '\n'
        output += 'приложение: ' + self.__application_version + '\n'
        if self.__process_type == 'serial':
            output += 'задача создана в режиме очереди' + '\n'
        elif self.__process_type == 'parallel':
            output += 'задача создана в параллельном режиме' + '\n'
        output += 'количество потоков в задаче: ' + str(self.__threads) + '\n'

        return output

    def solve(self):
        from subprocess import Popen
        import os
        if not os.path.isfile(self.__input_file):
            raise FileNotFoundError(self.__input_file)

        print("запущен расчёт fluent задачи \"" + self.__input_file + "\"")
        # составляем список команд и аттрибутов для запуска
        application = ['\"%AWP_ROOT' + self.__application_version
                       + '%\\CFD-Post\\bin\\cfdpost.exe\"',
                       '-batch', self.__input_file,
                       # '-outdir', self.__working_directory_path,
                       # '-name', self.__report_file_name,
                       # '-report', self.__report_file_name,
                       '-results', self.__results_file_name]

        # создание процесса по сконфигурированному application
        if self.__process_type == 'serial':
            # при создании процесса список application превращается в строку
            self.__process = Popen(' '.join(application), shell=True).wait()
            print("закончена обработка результатов " + self.__input_file + "\"")
        elif self.__process_type == 'parallel':
            # при создании процесса список application превращается в строку
            self.__process = Popen(' '.join(application), shell=True)

    @property
    def input_file(self):
        return self.__input_file

    @input_file.setter
    def input_file(self, file):
        self.__input_file = file

    @property
    def counter(self):
        return CFDPostTask.__counter

    @property
    def log_file_name(self):
        return self.__log_file_name

    @log_file_name.setter
    def log_file_name(self, name):
        self.__log_file_name = name

    @property
    def report_file_name(self):
        return self.__report_file_name

    @report_file_name.setter
    def report_file_name(self, name):
        self.__report_file_name = name

    @property
    def parameters_file_name(self):
        return self.__parameters_file_name

    @parameters_file_name.setter
    def parameters_file(self, name):
        self.__parameters_file_name = name

    @property
    def results_file_name(self):
        return self.__results_file_name

    @results_file_name.setter
    def results_file_name(self, name):
        self.__results_file_name = name

    @property
    def application_version(self):
        return self.__application_version

    @application_version.setter
    def application_version(self, name):
        self.__application_version = name

    @property
    def working_directory_path(self):
        return self.__working_directory_path

    @working_directory_path.setter
    def working_directory_path(self, name):
        self.__working_directory_path = name

    @property
    def threads(self):
        return self.__threads

    @threads.setter
    def threads(self, threads):
        self.__threads = str(threads)

