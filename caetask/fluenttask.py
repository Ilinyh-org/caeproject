import os
import shutil
import fnmatch
import tempfile
from subprocess import Popen

from caetask.caetask import CAETask, log_execution_time


class FluentTask(CAETask):
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
        # self.__working_directory_path = os.path.abspath(os.curdir)
        self._temporary_directory_path = None
        self._application_version = "212"
        self._dimension = "2d"
        self._graphics_regime = 'g'
        self._threads = '2'
        self._process_type = 'serial'
        self._process = None

    def __repr__(self):
        return self._task_name

    def __str__(self):
        output = super().__str__()
        if self._temporary_directory_path:
            output += 'путь временной директории: ' + self._temporary_directory_path + '\n'
        if self._results_file_name:
            output += 'файл результатов: ' + self._results_file_name + '\n'
        output += 'количество потоков в задаче: ' + str(self._threads) + '\n'
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
                          "Рекомендуем включить Режим Разрботчика. Сейчас будет создана жёсткая ссылка")
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
    def solve(self, cleanup=True):
        tempdir = tempfile.TemporaryDirectory(dir=self._temporary_directory_path)

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

        print("запущен расчёт Fluent задачи \"" +
              os.path.basename(self._input_file) + "\"" +
              " во временной директории " +
              os.path.basename(tempdir.name))

        application = [f'"{os.path.join('%AWP_ROOT' + self._application_version + '%',
                                        'fluent',
                                        'ntbin',
                                        'win64',
                                        'fluent.exe')}"',
                       self._dimension,
                       # '-r', self.__application_version[0:2] + '.' + self.__application_version[2:3] + '.0',
                       *(['-' + self._graphics_regime] if self._graphics_regime is not None else []),  # run without graphics
                       '-i', os.path.basename(self._input_file)]

        # создание ссылок или копирование дополнительных нетекстовых файлов
        self.__organize_additional_link_files(tempdir)

        # создание процесса по сконфигурированному application
        if self._process_type == 'serial':
            # при создании процесса список application превращается в строку
            with open(os.path.join(tempdir.name, self._log_file), 'w') as f:
                self._process = Popen(' '.join(application),
                                      shell=True,
                                      stdout=f,
                                      cwd=tempdir.name).wait()
            print("закончен расчёт ансис задачи " +
                  self._task_name +
                  " во временной директории " +
                  os.path.basename(tempdir.name))
        elif self._process_type == 'parallel':
            # при создании процесса список application превращается в строку
            self._process = Popen(' '.join(application), shell=True)

        # делаем проверку на регулярные выражения и расширяем список файлов с их учётом
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

        # переносим результаты в папку результатов
        for file in self._results_files_names:
            try:
                shutil.copy2(os.path.join(tempdir.name, file), self.__results_dir_path)
                print(f"Файл {file} fluent задачи {self._task_name} скопирован из "
                      f"{os.path.basename(tempdir.name)} в {os.path.basename(self.__results_dir_path)}")
            except OSError:
                print(f"Файл {file} не найден для копирования в {self.__results_dir_path}")

        if cleanup:
            tempdir.cleanup()
        return self

    @property
    def dimension(self):
        return self._dimension

    @dimension.setter
    def dimension(self, dimension):
        if dimension not in ["2d", "3d", "2ddp", "3ddp"]:
            raise ValueError("Неизвестный тип размерности задачи: " + dimension)
        self._dimension = dimension

    @property
    def threads(self):
        return self._threads

    @threads.setter
    def threads(self, threads):
        self._threads = str(threads)

