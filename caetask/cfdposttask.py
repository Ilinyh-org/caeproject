from caetask.caetask import CAETask
from subprocess import Popen
import os


class CFDPostTask(CAETask):
    def __init__(self, task_name='task'):
        super().__init__(task_name)
        self._task_name = task_name
        self._input_file = ''
        self._input_file_code = ''
        self._log_file = task_name + '.log'
        self._parameters_file_name = ''
        self._parameters_file_code = ''
        self._results_file_name = None
        self._results_files_names = []
        self._working_directory_path = os.path.abspath(os.curdir)
        self._application_version = "212"
        self._process_type = 'serial'
        self._process = None

    def __repr__(self):
        return self._task_name

    def __str__(self):
        output = super().__str__()
        output += 'путь рабочей директории: ' + self._working_directory_path + '\n'
        if self._results_file_name:
            output += 'файл результатов (входных): ' + self._results_file_name + '\n'
        return output

    def solve(self):
        if self._parameters_file_name:
            with open(os.path.join(os.path.abspath(self._working_directory_path),
                                   os.path.basename(self._parameters_file_name)), 'w') as f:
                f.writelines(self._parameters_file_code)
        if self._input_file:
            with open(os.path.join(os.path.abspath(self._working_directory_path),
                                   os.path.basename(self._input_file)), 'w') as f:
                f.writelines(self._input_file_code)
        print(f"запущен расчёт cfdpost задачи {os.path.basename(self._input_file)}")
        # составляем список команд и аттрибутов для запуска
        application = [f'{os.path.join('"%AWP_ROOT' + self._application_version + '%"',
                                       'CFD-Post',
                                       'bin',
                                       'cfdpost.exe')}',
                       '-batch', os.path.basename(self._input_file)]
        if self._results_file_name:
            application.append('-results')
            application.append(self._results_file_name)

        # создание процесса по сконфигурированному application
        if self._process_type == 'serial':
            # при создании процесса список application превращается в строку
            self._process = Popen(' '.join(application),
                                  shell=True,
                                  cwd=self._working_directory_path).wait()
            print(f"закончена обработка результатов {os.path.basename(self._input_file)}")
        elif self._process_type == 'parallel':
            # при создании процесса список application превращается в строку
            self._process = Popen(' '.join(application), shell=True)
