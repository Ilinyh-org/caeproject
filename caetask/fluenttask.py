import os
import shutil
import fnmatch
import tempfile
from subprocess import Popen

from caetask.caetask import CAETask


class FluentTask(CAETask):
    __counter = 0

    def __init__(self, task_name='task' + str(__counter)):
        self.__task_name = task_name
        self.__input_file = ''
        self.__input_file_code = ''
        self.__log_file = task_name + '.log'
        self.__parameters_file = ''
        self.__parameters_file_code = ''
        self.__results_file_name = ''
        self.__results_files_names = []
        self.__additional_text_files = []
        self.__additional_text_files_codes = []
        self.__additional_link_files = []
        self.__copy_link_files = False
        self.__results_dir_path = os.path.abspath(os.curdir)
        self.__geometry_file_name = ''
        self.__working_directory_path = os.path.abspath(os.curdir)
        self.__temporary_directory_path = None
        self.__application_version = "212"
        self.__dimension = "2d"
        self.__graphics_regime = 'g'
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
        output += 'файл логов: ' + self.__log_file + '\n'
        output += 'файл параметров: ' + self.__parameters_file + '\n'
        if self.__temporary_directory_path:
            output += 'путь временной директории: ' + self.__temporary_directory_path + '\n'
        if self.__working_directory_path:
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

    def __organize_additional_link_files(self, tempdir):
        # добавление ссылок на дополнительные файлы
        for file in self.__additional_link_files:
            src = file
            dst = os.path.join(tempdir.name, os.path.basename(file))
            if self.__copy_link_files:
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

    def solve(self, cleanup=True):
        tempdir = tempfile.TemporaryDirectory(dir=self.__temporary_directory_path)

        # чтение исходных файлов и запись их в рабочей директории
        if self.__parameters_file:
            with open(os.path.join(tempdir.name, os.path.basename(self.__parameters_file)), 'w') as f:
                f.writelines(self.__parameters_file_code)
        if self.__input_file:
            with open(os.path.join(tempdir.name, os.path.basename(self.__input_file)), 'w') as f:
                f.writelines(self.__input_file_code)

        for file in self.__additional_text_files:
            with open(os.path.join(tempdir.name, os.path.basename(file[0])), 'w') as f:
                f.writelines(file[1])

        print("запущен расчёт Fluent задачи \"" +
              os.path.basename(self.__input_file) + "\"" +
              " во временной директории " +
              os.path.basename(tempdir.name))

        application = [f'"{os.path.join('%AWP_ROOT' + self.__application_version + '%',
                                        'fluent',
                                        'ntbin',
                                        'win64',
                                        'fluent.exe')}"',
                       self.__dimension,
                        # '-r', self.__application_version[0:2] + '.' + self.__application_version[2:3] + '.0',
                       *(['-' + self.__graphics_regime] if self.__graphics_regime is not None else []), # run without graphics
                       '-i', os.path.basename(self.__input_file)]

        # создание ссылок или копирование дополнительных нетекстовых файлов
        self.__organize_additional_link_files(tempdir)

        # создание процесса по сконфигурированному application
        if self.__process_type == 'serial':
            # при создании процесса список application превращается в строку
            with open(os.path.join(tempdir.name, self.__log_file), 'w') as f:
                self.__process = Popen(' '.join(application),
                                       shell=True,
                                       stdout=f,
                                       cwd=tempdir.name).wait()
            print("закончен расчёт ансис задачи " +
                  self.__task_name +
                  " во временной директории " +
                  os.path.basename(tempdir.name))
        elif self.__process_type == 'parallel':
            # при создании процесса список application превращается в строку
            self.__process = Popen(' '.join(application), shell=True)

        # делаем проверку на регулярные выражения и расширяем список файлов с их учётом
        results_files_names_to_add = []
        results_files_names_to_remove = []
        for file in self.__results_files_names:
            if any(ch in file for ch in ['*', '?', '+']):
                try:
                    for f in os.listdir(tempdir.name):
                        if fnmatch.fnmatch(f, file):
                            results_files_names_to_add.append(f)
                    results_files_names_to_remove.append(file)
                except Exception:
                    pass
        self.__results_files_names.extend(results_files_names_to_add)
        for file in results_files_names_to_remove:
            self.__results_files_names.remove(file)

        # переносим результаты в папку результатов
        for file in self.__results_files_names:
            try:
                shutil.copy2(os.path.join(tempdir.name, file), self.__results_dir_path)
                print(f"Файл {file} fluent задачи {self.__task_name} скопирован из "
                      f"{os.path.basename(tempdir.name)} в {os.path.basename(self.__results_dir_path)}")
            except OSError:
                print(f"Файл {file} не найден для копирования в {self.__results_dir_path}")

        if cleanup:
            tempdir.cleanup()
        return self


    @property
    def input_file(self):
        return self.__input_file

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
        return FluentTask.__counter

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
    def additional_text_files(self):
        return self.__additional_text_files

    @additional_text_files.setter
    def additional_text_files(self, flist):
        if type(flist) is not list:
            flist = [flist]
        for file in flist:
            try:
                with open(file, encoding="utf-8") as f:
                    self.__additional_text_files.append((file, f.readlines()))
            except FileNotFoundError:
                raise FileNotFoundError(os.path.abspath(file) + " не найден")
            except UnicodeDecodeError:
                raise UnicodeDecodeError(f"Ошибка в кодировке файла {os.path.abspath(file)}")

    @property
    def additional_link_files(self):
        return self.__additional_link_files

    @additional_link_files.setter
    def additional_link_files(self, flist):
        if type(flist) is not list:
            flist = [flist]
        for file in flist:
            self.__additional_link_files.append(os.path.abspath(file))

    @property
    def copy_link_files(self):
        return self.__copy_link_files

    @copy_link_files.setter
    def copy_link_files(self, copy_link_files):
        if isinstance(copy_link_files, bool):
            self.__copy_link_files = copy_link_files

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
    def temporary_directory_path(self):
        return self.__temporary_directory_path

    @temporary_directory_path.setter
    def temporary_directory_path(self, path):
        self.__temporary_directory_path = os.path.abspath(path)

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

