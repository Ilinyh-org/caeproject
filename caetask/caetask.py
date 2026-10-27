"""Abstract base class for CAE solver tasks.

Provides :class:`CAETask`, which wraps a main input file with an
optional parameters file and additional text/link files, prepares
them into a run directory, tracks per-class instance counts, and
serializes itself via ``SERIALIZABLE_FIELDS``. Also provides the
:func:`log_execution_time` decorator used by concrete ``solve``
implementations.
"""
import os
import shutil
import tempfile
from abc import ABC, abstractmethod
import time
import datetime
import functools
import json
import sys
from pathlib import Path

from core.serialization import Serializable


def check_attribute(class_object):
    """Raise AttributeError unless the caller's property is backed by a private attribute.

    Uses the calling function's name (via ``sys._getframe``) and checks
    that ``class_object`` has the corresponding ``_<name>`` attribute,
    guarding properties that only concrete subclasses define.
    """
    attr_name = sys._getframe(1).f_code.co_name

    private_name = f'_{attr_name}'
    if not hasattr(class_object, private_name):
        raise AttributeError(
            f"The {type(class_object).__name__} doesn't support {attr_name} attribute"
        )


class CAETask(ABC, Serializable):
    """Abstract base class for all CAE solver tasks.

    A task references its main input file, optional parameters file,
    and additional text/link files; loads and prepares them into the
    run directory; and exposes configurable properties (name, log
    file, application version, directories). Subclasses implement
    :meth:`solve` to launch the actual solver.
    """

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
        self._additional_text_files_codes = None
        self._additional_link_files = None
        self._copy_link_files = None

        self._process = None
        self._increment_counter()

    @property
    def case(self):
        """The case this task belongs to, or None if unattached."""
        return self._case

    @classmethod
    def create_new(
            cls,
            name: str | None = None,
            base_path: Path | None = None,
    ):
        """Create a task instance with the given name under ``base_path``."""
        base_path = cls.normalize_path(base_path)

        return cls(
            base_path=base_path,
            name=name,
        )

    def to_dict(self):
        """Prepare data for serialization."""
        data = super().to_dict()

        # input file
        if self.case:
            data.update({"input_file": str(self.input_file.relative_to(self.case.path))})
        else:
            data.update({"input_file": str(self.input_file)})

        # additional link files
        if self.additional_link_files:
            additional_link_files = []
            for additional_link_file in self.additional_link_files:
                if self.case:
                    additional_link_files.append(str(additional_link_file.relative_to(self.case.path)))
                else:
                    additional_link_files.append(str(additional_link_file))
            data.update({"additional_link_files": additional_link_files})
        else:
            data.update({"additional_link_files": self.additional_link_files})

        # log file
        data.update({"log_file_name": self.log_file_name})

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

    def load_files(self):
        """Resolve and read the input and parameters files.

        External files are copied into the case directory; each file's
        resolved path and text contents are cached for the run.
        """
        self._input_file, self._input_file_code = (
            self._prepare_file(self._input_file)
        )

        self._parameters_file, self._parameters_file_code = (
            self._prepare_file(self._parameters_file)
        )

    def _create_files_in_running_dir(
            self,
            dst_path: Path | str | tempfile.TemporaryDirectory | None) -> Path:

        if isinstance(dst_path, str):
            dst_path = Path(dst_path)
        elif isinstance(dst_path, tempfile.TemporaryDirectory):
            dst_path = Path(dst_path.name)

        if self._parameters_file:
            with open(dst_path / self._parameters_file.name, 'w', encoding="utf-8") as f:
                f.writelines(self._parameters_file_code)
        if self._input_file:
            with open(dst_path / self._input_file.name, 'w', encoding="utf-8") as f:
                f.writelines(self._input_file_code)
        if self._additional_text_files:
            for file in self._additional_text_files:
                with open(dst_path / file[0], 'w', encoding="utf-8") as f:
                    f.writelines(file[1])

        return dst_path

    def _organize_additional_link_files(self, tempdir):
        # добавление ссылок на дополнительные файлы
        if self.additional_link_files is None:
            return

        for file in self._additional_link_files:
            src = file
            dst = Path(tempdir.name) / Path(file).name
            if self._copy_link_files:
                shutil.copy2(src, tempdir.name)
                continue
            try:  # создание символьной ссылки
                os.symlink(src, dst, target_is_directory=False, dir_fd=None)
            except OSError as e:
                if e.winerror == 1314:
                    print("Ошибка 1314: Недостаточно прав для создания символьной ссылки. \n"
                          "Рекомендуем включить Режим Разработчика. Сейчас будет создана жёсткая ссылка")
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
        """Zero the instance counters: all classes when called on CAETask, else only this class."""
        if cls is CAETask:
            for key in cls._class_counts:
                cls._class_counts[key] = 0
        else:
            CAETask._class_counts[cls] = 0

    @abstractmethod
    def solve(self):
        """Run the task; implemented by concrete task subclasses."""
        ...

    @classmethod
    def count(cls):
        """Number of currently living instances of this task class."""
        return CAETask._class_counts.get(cls, 0)

    @property
    def name(self):
        """Task name (the setter coerces the value to ``str``)."""
        return self._name

    @name.setter
    def name(self, name):
        self._name = str(name)

    @property
    def input_file(self) -> Path | None:
        """Path to the task's main input file, or None."""
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
        """Resolved path of the prepared input file, set by :meth:`load_files`."""
        return self._input_file_path

    @property
    def log_file_name(self) -> str:
        """Log file name, defaulting to ``<task name>.log``."""
        if self._log_file_name is None:
            self._log_file_name = f"{self.name}.log"
        return self._log_file_name

    @log_file_name.setter
    def log_file_name(self, name: str):
        self._log_file_name = name

    @property
    def parameters_file(self) -> Path | None:
        """Path to the task's parameters file, or None."""
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
        """Resolved path of the prepared parameters file, set by :meth:`load_files`."""
        return self._parameters_file_path

    @property
    def additional_text_files(self):
        """Text files inlined into the run directory as ``(name, lines)`` tuples."""
        check_attribute(self)
        return self._additional_text_files

    @additional_text_files.setter
    def additional_text_files(self, flist: Path | list[Path] | None):
        check_attribute(self)

        if flist is None:
            return

        if self._additional_text_files is None:
            self._additional_text_files = []

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
        """Extra files linked (or copied) into the run directory at solve time."""
        check_attribute(self)
        return self._additional_link_files

    @additional_link_files.setter
    def additional_link_files(self, flist: list[Path] |  list[str] | Path):
        check_attribute(self)

        if flist is None:
            return

        if type(flist) is not list:
            flist = [flist]

        if self._additional_link_files is None:
            self._additional_link_files = []



        for file in flist:
            file_path = Path(file)
            if not file_path.is_absolute():
                if self.case:
                    file_path = self.case.path / file_path
            self._additional_link_files.append(file_path)

    @property
    def copy_link_files(self):
        """If True, copy additional link files instead of symlinking them."""
        check_attribute(self)
        return self._copy_link_files

    @copy_link_files.setter
    def copy_link_files(self, copy_link_files):
        check_attribute(self)
        if isinstance(copy_link_files, bool):
            self._copy_link_files = copy_link_files

    @property
    def results_file_name(self):
        """Optional explicit single result file name."""
        check_attribute(self)
        return self._results_file_name

    @results_file_name.setter
    def results_file_name(self, name: str):
        check_attribute(self)
        self._results_file_name = name

    @property
    def results_files_names(self):
        """Names of the result files produced by the task (always a list)."""
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
        """Target application version string (e.g. ``"212"``)."""
        check_attribute(self)
        return self._application_version

    @application_version.setter
    def application_version(self, name: str):
        check_attribute(self)
        self._application_version = name

    @property
    def working_directory(self) -> Path:
        """Directory the task runs in, or None if unset."""
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
        """Parent directory for the task's temporary run directories, or None."""
        check_attribute(self)
        return self._temporary_directory

    @temporary_directory.setter
    def temporary_directory(self, path: Path):
        check_attribute(self)
        self._temporary_directory = path

    @property
    def results_directory(self):
        """Directory result files are copied into after the run, or None."""
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

