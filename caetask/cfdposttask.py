from caetask import CAETask
from subprocess import Popen
import os


class CFDPostTask(CAETask):
    def __init__(
            self,
            name='task',
            base_path: str | None = None
    ):
        super().__init__(name, base_path)
        self._name = name
        self._log_file_name = name + '.log'
        self._results_file_name = None
        self._results_files_names = []
        self._working_directory = os.path.abspath(os.curdir)
        self._application_version = "212"

    def __repr__(self):
        return self._name

    def __str__(self):
        output = super().__str__()
        output += 'путь рабочей директории: ' + self._working_directory + '\n'
        if self._results_file_name:
            output += 'файл результатов (входных): ' + self._results_file_name + '\n'
        return output

    def solve(self):
        self.load_inputs()

        if self._parameters_file:
            with open(os.path.join(os.path.abspath(self._working_directory),
                                   os.path.basename(self._parameters_file)), 'w') as f:
                f.writelines(self._parameters_file_code)
        if self._input_file:
            with open(os.path.join(os.path.abspath(self._working_directory),
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
        self._process = Popen(' '.join(application),
                              shell=True,
                              cwd=self._working_directory).wait()
        print(f"закончена обработка результатов {os.path.basename(self._input_file)}")
