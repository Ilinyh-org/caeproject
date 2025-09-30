from abc import ABCMeta, abstractmethod


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


class CFDPostTask(CAETask):
    __counter = 0

    def __init__(self, task_name='task' + str(__counter)):
        self.__task_name = task_name
        self.__input_file = ''
        self.__log_file_name = task_name + '.log'
        self.__parameters_file_name = ''
        self.__results_file_name = ''
        self.__geometry_file_name = ''
        self.__working_directory_path = '../'
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
        self.__working_directory_path = '../'
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

