
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
            f"The {type(class_object).__name__} doesn't support {attr_name} attribute"
        )


class CAETask(ABC, Serializable):
    _class_counts = {}  # Словарик для хранения счётчиков по классам

    def __init__(
            self,
            name: str = 'task',
            base_path: Path | None = None,
            input_file: Path | str | None = None,
            parameters_file: Path | str | None = None,
            results_files_names: list[str] | None = None
    ):
        super().__init__(base_path, name)
        self._name = name

        self._case = None

        self._working_directory = None
        self._temporary_directory = None
        self._results_directory = None

        self._log_file_name = None

        self._results_file_name = None

        # User-provided file references
        self.input_file = input_file
        self.parameters_file = parameters_file
        self.results_files_names = results_files_names

        # Actual files prepared for execution
        self._input_file_path: Path | None = None
        self._parameters_file_path: Path | None = None

        # Loaded file contents
        self._input_file_code: list[str] | None = None
        self._parameters_file_code: list[str] | None = None

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

    @classmethod
    def from_dict(
            cls,
            data: dict,
            *,
            base_path: Path | None = None,
            name: str | None = None
    ):
        base_path = cls.normalize_path(base_path)

        obj = cls(base_path=base_path, name=name)

        for field in cls.SERIALIZABLE_FIELDS:
            if field in data:
                setattr(obj, field, data[field])

        return obj

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
        output += 'исполняемый файл: ' + str(self._input_file.name) + '\n'
        if self._parameters_file:
            output += 'файл параметров: ' + self._parameters_file + '\n'
        output += 'файл логов: ' + self.log_file_name + '\n'
        output += 'версия приложения: ' + self._application_version + '\n'
        return output

    def _prepare_file(
            self,
            file: Path | None,
    ) -> tuple[Path | None, list[str] | None]:

        if file is None:
            return None, None

        file = file.expanduser()

        # Resolve relative paths.
        if not file.is_absolute():
            if self.case is not None:
                source = self.case.path / file
            else:
                source = Path.cwd() / file
        else:
            source = file

        source = source.resolve()

        if not source.is_file():
            raise FileNotFoundError(
                f"{source} is not found"
            )

        # No case: the source itself is the prepared file.
        if self.case is None:
            with open(source, encoding="utf-8") as f:
                code = f.readlines()

            return source, code

        case_path = self.case.path.resolve()

        # File is already inside the case directory.
        try:
            source.relative_to(case_path)
            destination = source
        except ValueError:
            # External file -> copy it into the case directory.
            destination = case_path / source.name

            import shutil
            shutil.copy2(source, destination)

        with open(destination, encoding="utf-8") as f:
            code = f.readlines()

        return destination, code

    def load_inputs(self):
        self._input_file, self._input_file_code = (
            self._prepare_file(self._input_file)
        )

        self._parameters_file, self._parameters_file_code = (
            self._prepare_file(self._parameters_file)
        )

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
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = str(name)

    @property
    def input_file(self) -> Path | None:
        return self._input_file

    @input_file.setter
    def input_file(self, file: Path | str | None):
        if file is None:
            self._input_file = None
            return
        # if isinstance(file, str):
        #     if self.case:
        #         file = self.case.path / file
        #     else:
        #         file = Path.cwd() / file

        self._input_file = Path(file)
        self._input_file_path = None
        self._input_file_code = None

    @property
    def input_file_path(self) -> Path | None:
        return self._input_file_path

    @property
    def log_file_name(self) -> str:
        if self._log_file_name is None:
            self._log_file_name = f"{self.name}.log"
        return self._log_file_name

    @log_file_name.setter
    def log_file_name(self, name: str):
        self._log_file_name = name

    @property
    def parameters_file(self) -> Path | None:
        return self._parameters_file

    @parameters_file.setter
    def parameters_file(self, file: Path | str | None):
        if file is None:
            self._parameters_file = None
            return

        # if isinstance(file, str):
        #     if self.case:
        #         file = self.case.path / file
        #     else:
        #         file = Path.cwd() / file

        self._parameters_file = Path(file)
        self._parameters_file_path = None
        self._parameters_file_code = None

    @property
    def parameters_file_path(self) -> Path | None:
        return self._parameters_file_path

    @property
    def additional_text_files(self):
        check_attribute(self)
        return self._additional_text_files

    @additional_text_files.setter
    def additional_text_files(self, flist: Path | list[Path] | None):
        check_attribute(self)
        if type(flist) is not list:
            flist = [flist]
        for file in flist:
            try:
                with open(file, encoding="utf-8") as f:
                    self._additional_text_files.append((file.name, f.readlines()))
            except FileNotFoundError:
                raise FileNotFoundError(file.name + " не найден")
            except UnicodeDecodeError:
                raise UnicodeDecodeError(f"Ошибка в кодировке файла {file.absolute()}")

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
        return self._results_files_names

    @results_files_names.setter
    def results_files_names(self, flist: list[Path] | Path | None):
        if flist is None:
            flist = []
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
        if isinstance(path, str):
            path = Path(path)
        self._working_directory = path

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

