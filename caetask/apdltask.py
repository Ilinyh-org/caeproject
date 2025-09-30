import os
import shutil
import tempfile
from subprocess import Popen

from caetask.caetask import CAETask


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
        self.__additional_text_files = []
        self.__additional_text_files_codes = []
        self.__additional_link_files = []
        self.__copy_link_files = False
        self.__results_dir_path = os.path.abspath(os.curdir)
        self.__geometry_file_name = ''
        self.__working_directory_path = os.path.abspath(os.curdir)
        self.__temporary_directory_path = None
        self.__application_version = "212"
        self.__cores = '2'
        self.__new_parameter_name = None
        self.__new_parameter_value = None
        self.__process_type = 'serial'
        self.__memory_size = '2048'
        self.__database_size = '1024'
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
        if self.__temporary_directory_path:
            output += 'путь временной директории: ' + self.__temporary_directory_path + '\n'
        if self.__working_directory_path:
            output += 'путь рабочей директории: ' + self.__working_directory_path + '\n'
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
            with open(tempdir.name + "\\" + os.path.basename(self.__parameters_file), 'w') as f:
                f.writelines(self.__parameters_file_code)
        if self.__input_file:
            with open(tempdir.name + "\\" + os.path.basename(self.__input_file), 'w') as f:
                f.writelines(self.__input_file_code)

        for file in self.__additional_text_files:
            with open(tempdir.name + "\\" + os.path.basename(file[0]), 'w') as f:
                f.writelines(file[1])

        print("запущен расчёт ансис задачи \"" +
              os.path.basename(self.__input_file) + "\"" +
              " во временной директории " +
              os.path.basename(tempdir.name))

        # составляем список команд и аттрибутов для запуска
        # для запуска используется переменная среды типа ansys180_dir
        application = ['"%ansys' + self.__application_version
                       + '_dir%\\bin\\winx64\\'
                       + 'ansys' + self.__application_version + '"',
                       '-b',
                       '-m', self.__memory_size,
                       '-db', self.__database_size,
                       '-dir', tempdir.name,
                       '-np', self.__cores,
                       '-j', self.__task_name,
                       '-i', os.path.basename(self.__input_file),
                       '-o', tempdir.name + "\\" + self.__log_file,
                       '-gtmfile', self.__geometry_file_name,
                       '-resfile', self.__results_file_name,
                       '-parfile', os.path.basename(self.__parameters_file)]
        if self.__new_parameter_name:  # no new parameters
            if type(self.__new_parameter_name) == list:  # list of  new parameter
                for a, b in zip(self.__new_parameter_name, self.__new_parameter_value):
                    application.append('-' + a)
                    application.append(b)
            else:  # one new parameter
                application.append('-' + self.__new_parameter_name)
                application.append(self.__new_parameter_value)

        # создание ссылок или копирование дополнительных нетекстовых файлов
        self.__organize_additional_link_files(tempdir)

        # создание процесса по сконфигурированному application
        if self.__process_type == 'serial':
            # при создании процесса список application превращается в строку
            self.__process = Popen(' '.join(application), shell=True).wait()
            print("закончен расчёт ансис задачи " +
                  self.__task_name +
                  " во временной директории " +
                  os.path.basename(tempdir.name))
        elif self.__process_type == 'parallel':
            # при создании процесса список application превращается в строку
            self.__process = Popen(' '.join(application), shell=True)

        # переносим результаты в папку результатов
        for file in self.__results_files_names:
            try:
                shutil.copy2(tempdir.name + "\\" + file, self.__results_dir_path)
                print(f"Файл {file} ансис задачи {self.__task_name} скопирован из {os.path.basename(tempdir.name)} в {os.path.basename(self.__results_dir_path)}")
            except OSError:
                print(f"Файл {file} не найден для копирования в {self.__results_dir_path}")

        if cleanup:
            tempdir.cleanup()
        return self

    # @caetask.input_file_name
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
            try:
                with open(file, encoding="utf-8") as f:
                    self.__additional_link_files.append(os.path.abspath(file))
            except FileNotFoundError:
                raise FileNotFoundError(os.path.abspath(file) + " не найден")

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
        try:
            with open(file) as f:
                self.__parameters_file_code = f.readlines()
            self.__parameters_file = file
        except FileNotFoundError:
            raise FileNotFoundError(os.path.abspath(file) + " не найден")

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
    def temporary_directory_path(self):
        return self.__temporary_directory_path

    @temporary_directory_path.setter
    def temporary_directory_path(self, path):
        self.__temporary_directory_path = os.path.abspath(path)

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
    def memory_size(self):
        return self.__memory_size

    @memory_size.setter
    def memory_size(self, memory_size):
        self.__memory_size = str(memory_size)

    @property
    def database_size(self):
        return self.__database_size

    @database_size.setter
    def database_size(self, database_size):
        self.__database_size = str(database_size)

    @property
    def status(self):
        return self.__process.poll()
