import os
from abc import ABC, abstractmethod
import time
import datetime
import functools
import json
import sys


def check_attribute(class_object):
    attr_name = sys._getframe(1).f_code.co_name

    private_name = f'_{attr_name}'
    if not hasattr(class_object, private_name):
        raise AttributeError(
            f"Объект {type(class_object).__name__} не поддерживает атрибут {attr_name}"
        )


class CAETask(ABC):
    _class_counts = {}  # Словарик для хранения счётчиков по классам

    def __init__(self, task_name='task'):
        self._log_file = None
        self._input_file = None
        self._input_file_code = None
        self._task_name = task_name
        self._increment_counter()

    def __del__(self):
        try:
            self._decrement_counter()
        except (AttributeError, KeyError):
            # Игнорируем ошибки, если счётчик уже удалён или класс не зарегистрирован
            pass

    def __str__(self):
        output = 'имя задачи: ' + self._task_name + '\n'
        output += 'исполняемый файл: ' + str(os.path.basename(self._input_file)) + '\n'
        if self._parameters_file_name:
            output += 'файл параметров: ' + self._parameters_file_name + '\n'
        output += 'файл логов: ' + self._log_file + '\n'
        output += 'версия приложения: ' + self._application_version + '\n'
        return output

    @classmethod
    def _increment_counter(cls):
        """Увеличивает счётчик для конкретного класса"""
        cls_name = cls.__name__
        if cls_name not in CAETask._class_counts:
            CAETask._class_counts[cls_name] = 0
        CAETask._class_counts[cls_name] += 1

    @classmethod
    def _decrement_counter(cls):
        """Уменьшает счётчик для конкретного класса"""
        cls_name = cls.__name__
        if cls_name in CAETask._class_counts and CAETask._class_counts[cls_name] > 0:
            CAETask._class_counts[cls_name] -= 1

    @abstractmethod
    def solve(self):
        ...

    @property
    def task_name(self):
        return self._task_name

    @property
    def counter(self):
        return CAETask._class_counts.get(self.__class__.__name__, 0)

    @property
    def input_file(self):
        return self._input_file

    @input_file.setter
    def input_file(self, file):
        try:
            with open(file, encoding="utf-8") as f:
                self._input_file_code = f.readlines()
            self._input_file = file
        except FileNotFoundError:
            raise FileNotFoundError(os.path.abspath(file) + " не найден")

    @property
    def log_file(self):
        return self._log_file

    @log_file.setter
    def log_file(self, file):
        self._log_file = file

    @property
    def parameters_file(self):
        return self._parameters_file_name

    @parameters_file.setter
    def parameters_file(self, file):
        try:
            with open(file) as f:
                self._parameters_file_code = f.readlines()
            self._parameters_file_name = file
        except FileNotFoundError:
            raise FileNotFoundError(os.path.abspath(file) + " не найден")

    @property
    def additional_text_files(self):
        check_attribute(self)
        return self._additional_text_files

    @additional_text_files.setter
    def additional_text_files(self, flist):
        check_attribute(self)
        if type(flist) is not list:
            flist = [flist]
        for file in flist:
            try:
                with open(file, encoding="utf-8") as f:
                    self._additional_text_files.append((file, f.readlines()))
            except FileNotFoundError:
                raise FileNotFoundError(os.path.abspath(file) + " не найден")
            except UnicodeDecodeError:
                raise UnicodeDecodeError(f"Ошибка в кодировке файла {os.path.abspath(file)}")

    @property
    def additional_link_files(self):
        check_attribute(self)
        return self._additional_link_files

    @additional_link_files.setter
    def additional_link_files(self, flist):
        check_attribute(self)
        if type(flist) is not list:
            flist = [flist]
        for file in flist:
            self._additional_link_files.append(os.path.abspath(file))

    @property
    def copy_link_files(self):
        check_attribute(self)
        return self._copy_link_files

    @copy_link_files.setter
    def copy_link_files(self, copy_link_files):
        check_attribute(self)
        if isinstance(copy_link_files, bool):
            self._copy_link_files = copy_link_files

    @property
    def results_file_name(self):
        check_attribute(self)
        return self._results_file_name

    @results_file_name.setter
    def results_file_name(self, name):
        check_attribute(self)
        self._results_file_name = name

    @property
    def results_files_names(self):
        check_attribute(self)
        return self._results_files_names

    @results_files_names.setter
    def results_files_names(self, flist):
        check_attribute(self)
        if type(flist) is list:
            self._results_files_names = flist
        else:
            self._results_files_names = [flist]

    @property
    def application_version(self):
        check_attribute(self)
        return self._application_version

    @application_version.setter
    def application_version(self, name):
        check_attribute(self)
        self._application_version = name

    @property
    def working_directory_path(self):
        check_attribute(self)
        return self.__working_directory_path

    @working_directory_path.setter
    def working_directory_path(self, path):
        check_attribute(self)
        self.__working_directory_path = os.path.abspath(path)

    @property
    def temporary_directory_path(self):
        check_attribute(self)
        return self._temporary_directory_path

    @temporary_directory_path.setter
    def temporary_directory_path(self, path):
        check_attribute(self)
        self._temporary_directory_path = os.path.abspath(path)

    @property
    def results_directory_path(self):
        check_attribute(self)
        return self._results_directory_path

    @results_directory_path.setter
    def results_directory_path(self, path):
        check_attribute(self)
        self._results_directory_path = os.path.abspath(path)


def log_execution_time():
    """
    Декоратор: для каждой функции создаёт отдельный JSON‑лог‑файл.
    - При старте записывает начальную запись (status=running).
    - По завершении перезаписывает файл итоговой записью (success/error).
    - Лог‑файл назван по шаблону: <task_name>_<function_qualname>.json
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Формируем имя лог‑файла
            # Предполагаем, что первый аргумент (args[0]) — это экземпляр класса с атрибутом task_name
            task_name = args[0].task_name
            func_qualname = func.__qualname__.replace(".", "_")
            log_file = f"{task_name}_{func_qualname}.log"

            # Время начала
            start_time = time.time()
            start_dt = datetime.datetime.now()

            # Начальная запись (статус running)
            initial_log = {
                "function_name": func.__name__,
                "start_time": start_dt.isoformat(),
                "end_time": None,
                "duration_seconds": None,
                "status": "running"
            }

            # Записываем стартовую запись в JSON‑файл
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(initial_log, f, indent=4, ensure_ascii=False)

            try:
                # Выполняем функцию
                result = func(*args, **kwargs)

                # Время окончания
                end_time = time.time()
                end_dt = datetime.datetime.now()

                # Итоговая запись (статус success)
                final_log = {
                    "function_name": func.__name__,
                    "start_time": start_dt.isoformat(),
                    "end_time": end_dt.isoformat(),
                    "duration_seconds": round(end_time - start_time, 4),
                    "status": "success"
                }

                # Перезаписываем JSON‑файл итоговой записью
                with open(log_file, "w", encoding="utf-8") as f:
                    json.dump(final_log, f, indent=4, ensure_ascii=False)

                return result

            except Exception as e:
                # Время при ошибке
                end_dt = datetime.datetime.now()

                # Итоговая запись (статус error)
                error_log = {
                    "function_name": func.__name__,
                    "start_time": start_dt.isoformat(),
                    "end_time": end_dt.isoformat(),
                    "duration_seconds": round(time.time() - start_time, 4),
                    "status": f"error: {str(e)}"
                }

                # Перезаписываем JSON‑файл записью об ошибке
                with open(log_file, "w", encoding="utf-8") as f:
                    json.dump(error_log, f, indent=4, ensure_ascii=False)

                raise  # Пробрасываем исключение дальше

        return wrapper

    return decorator

