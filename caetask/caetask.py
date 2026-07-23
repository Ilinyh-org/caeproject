import os
from abc import ABC, abstractmethod
import time
import datetime
import functools
import json
import sys
from pathlib import Path

from core.serialization import Serializable


def check_attribute(class_object):
    attr_name = sys._getframe(1).f_code.co_name

    private_name = f'_{attr_name}'
    if not hasattr(class_object, private_name):
        raise AttributeError(
            f"Объект {type(class_object).__name__} не поддерживает атрибут {attr_name}"
        )


class CAETask(ABC, Serializable):
    _class_counts = {}  # Словарик для хранения счётчиков по классам

    def __init__(
            self,
            name: str = 'task',
            base_path: Path | None = None
    ):
        super().__init__(base_path, name)

        self._case = None

        self._working_directory = None
        self._temporary_directory = None
        self._results_directory = None

        self._log_file_name = None
        self._input_file: Path | None = None
        self._input_file_code = None
        self._parameters_file: Path | None = None
        self._parameters_file_code = None

        self._additional_text_files = None
        self._copy_link_files = None

        self._process = None
        self._increment_counter()

    @property
    def case(self):
        return self._case

    @classmethod
    def create_new(
            cls,
            name: str | None = None,
            base_path: Path | None = None,
    ):
        base_path = cls.normalize_path(base_path)

        return cls(
            base_path=base_path,
            name=name,
        )

    def to_dict(self):
        """Prepare data for serialization."""
        data = super().to_dict()

        data.update({"log_file_name": self.log_file_name})

        data.update({"input_file": str(self.input_file)})

        return data

    @property
    def path(self) -> Path:
        return self.base_path

    def __del__(self):
        try:
            self._decrement_counter()
        except (AttributeError, KeyError):
            # Игнорируем ошибки, если счётчик уже удалён или класс не зарегистрирован
            pass

    def __str__(self):
        output = 'имя задачи: ' + self.name + '\n'
        output += 'исполняемый файл: ' + str(os.path.basename(self._input_file)) + '\n'
        if self._parameters_file:
            output += 'файл параметров: ' + self._parameters_file + '\n'
        output += 'файл логов: ' + self.log_file_name + '\n'
        output += 'версия приложения: ' + self._application_version + '\n'
        return output

    def load_inputs(self):
        #it has to be checked for the self.case case that path is in the case dir, if it's not, then the file has to be copied to the dir

        if self._input_file:
            try:
                with open(self._input_file, encoding="utf-8") as f:
                    self._input_file_code = f.readlines()
            except FileNotFoundError:
                raise FileNotFoundError(str(self._input_file.absolute()) + " is not found")
            if self.case and self._input_file.parent != self.case.path:  # copy file to the case dir
                input_file = self.case.path / self._input_file.name
                with open(input_file, "w", encoding="utf-8") as f:
                    f.writelines(self._input_file_code)
                self._input_file = input_file.relative_to(self.case.path)

        if self._parameters_file:
            try:
                with open(self._parameters_file, encoding="utf-8") as f:
                    self._parameters_file_code = f.readlines()
            except FileNotFoundError:
                raise FileNotFoundError(str(self._parameters_file.absolute()) + " is not found")
            if self.case:
                if self._parameters_file.parent != self.case.path:  # copy file to the case dir
                    parameters_file = self.case.path / self._parameters_file.name
                    with open(parameters_file, "w", encoding="utf-8") as f:
                        f.writelines(self._parameters_file_code)
                else:
                    parameters_file = self._parameters_file
                self._parameters_file = parameters_file.relative_to(self.case.path)


    @classmethod
    def _increment_counter(cls):
        """Увеличивает счётчик для конкретного класса"""
        if cls not in CAETask._class_counts:
            CAETask._class_counts[cls] = 0
        CAETask._class_counts[cls] += 1

    @classmethod
    def _decrement_counter(cls):
        """Уменьшает счётчик для конкретного класса"""
        if cls in CAETask._class_counts and CAETask._class_counts[cls] > 0:
            CAETask._class_counts[cls] -= 1

    @classmethod
    def reset(cls):
        if cls is CAETask:
            for key in cls._class_counts:
                cls._class_counts[key] = 0
        else:
            CAETask._class_counts[cls] = 0

    @abstractmethod
    def solve(self):
        ...

    @classmethod
    def count(cls):
        return CAETask._class_counts.get(cls, 0)

    @property
    def input_file(self):
        return self._input_file

    @input_file.setter
    def input_file(self, file: Path | str):
        if isinstance(file, str):
            if self.case:
                file = self.case.path / file
            else:
                file = Path.cwd() / file

        self._input_file = file

    @property
    def log_file_name(self) -> str:
        if self._log_file_name is None:
            self._log_file_name = f"{self.name}.log"
        return self._log_file_name

    @log_file_name.setter
    def log_file_name(self, name: str):
        self._log_file_name = name

    @property
    def parameters_file(self):
        return self._parameters_file

    @parameters_file.setter
    def parameters_file(self, file: Path | str):
        if isinstance(file, str):
            if self.case:
                file = self.case.path / file
            else:
                file = Path.cwd() / file

        self._parameters_file = file

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
                    self._additional_text_files.append((file.name, f.readlines()))
            except FileNotFoundError:
                raise FileNotFoundError(os.path.abspath(file) + " не найден")
            except UnicodeDecodeError:
                raise UnicodeDecodeError(f"Ошибка в кодировке файла {os.path.abspath(file)}")

    @property
    def additional_link_files(self):
        check_attribute(self)
        return self._additional_link_files

    @additional_link_files.setter
    def additional_link_files(self, flist: list[Path] | Path):
        check_attribute(self)
        if type(flist) is not list:
            flist = [flist]
        for file in flist:
            self._additional_link_files.append(file)

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
    def results_file_name(self, name: str):
        check_attribute(self)
        self._results_file_name = name

    @property
    def results_files_names(self):
        check_attribute(self)
        return self._results_files_names

    @results_files_names.setter
    def results_files_names(self, flist: list[Path] | Path):
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
    def application_version(self, name: str):
        check_attribute(self)
        self._application_version = name

    @property
    def working_directory(self) -> Path:
        check_attribute(self)
        return self._working_directory

    @working_directory.setter
    def working_directory(self, path: Path):
        check_attribute(self)
        self._working_directory = os.path.abspath(path)

    @property
    def temporary_directory(self):
        check_attribute(self)
        return self._temporary_directory

    @temporary_directory.setter
    def temporary_directory(self, path: Path):
        check_attribute(self)
        self._temporary_directory = path

    @property
    def results_directory(self):
        check_attribute(self)
        return self._results_directory

    @results_directory.setter
    def results_directory(self, path: Path | str | None):
        check_attribute(self)
        if isinstance(path, str):
            path = Path(path)
        self._results_directory = path


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
            task_name = args[0].name
            results_directory_path = args[0].results_directory

            func_qualname = func.__qualname__.replace(".", "_")
            log_file = f"{task_name}_{func_qualname}.log"
            log_file_full_path = results_directory_path / log_file

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
            with open(log_file_full_path, "w", encoding="utf-8") as f:
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
                with open(log_file_full_path, "w", encoding="utf-8") as f:
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
                with open(log_file_full_path, "w", encoding="utf-8") as f:
                    json.dump(error_log, f, indent=4, ensure_ascii=False)

                raise  # Пробрасываем исключение дальше

        return wrapper

    return decorator

