from caetask.caetask import CAETask
from subprocess import Popen
import os


class CFDPostTask(CAETask):
    __counter = 0

    def __init__(self, task_name='task' + str(__counter)):
        self.__task_name = task_name
        self.__input_file = ''
        self.__input_file_code = ''
        self.__log_file = task_name + '.log'
        self.__parameters_file_name = ''
        self.__parameters_file_code = ''
        self.__results_file_name = ''
        self.__report_file_name = task_name
        self.__results_files_names = []
        self.__working_directory_path = os.path.abspath(os.curdir)
        self.__application_version = "212"
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
        output += 'файл логов: ' + self.__log_file + '\n'
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
        if self.__parameters_file_name:
            with open(os.path.basename(self.__parameters_file_name), 'w') as f:
                f.writelines(self.__parameters_file_code)
        if self.__input_file:
            with open(os.path.basename(self.__input_file), 'w') as f:
                f.writelines(self.__input_file_code)
        print(f"запущен расчёт cfdpost задачи {os.path.basename(self.__input_file)}")
        # составляем список команд и аттрибутов для запуска
        application = ['\"%AWP_ROOT' + self.__application_version
                       + '%\\CFD-Post\\bin\\cfdpost.exe\"',
                       '-batch', os.path.basename(self.__input_file),
                       # '-outdir', self.__working_directory_path,
                       # '-name', self.__report_file_name,
                       # '-report', self.__report_file_name,
                       #'-results', self.__results_file_name
        ]

        # создание процесса по сконфигурированному application
        if self.__process_type == 'serial':
            # при создании процесса список application превращается в строку
            self.__process = Popen(' '.join(application),
                                   shell=True,
                                   cwd=self.__working_directory_path).wait()
            print(f"закончена обработка результатов {os.path.basename(self.__input_file)}")
        elif self.__process_type == 'parallel':
            # при создании процесса список application превращается в строку
            self.__process = Popen(' '.join(application), shell=True)

    @property
    def input_file(self):
        return self.__input_file

    # @caetask.input_file_name.setter
    @input_file.setter
    def input_file(self, file):
        try:
            with open(file, encoding="utf-8") as f:
                self.__input_file_code = f.readlines()
            self.__input_file = file
        except FileNotFoundError:
            raise FileNotFoundError(os.path.abspath(file) + " не найден")

    @property
    def counter(self):
        return CFDPostTask.__counter

    @property
    def log_file(self):
        return self.__log_file

    @log_file.setter
    def log_file(self, file):
        self.__log_file = file

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
