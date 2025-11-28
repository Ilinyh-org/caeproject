from abc import ABCMeta, abstractmethod
import time
import datetime
import functools
import json


class CAETask:
    __metaclass__ = ABCMeta

    def __init__(self, task_name='task'):
        self.__task_name = task_name

    @abstractmethod
    def solve(self):
        ...

    @property
    def task_name(self):
        return self.__task_name

    @property
    @abstractmethod
    def input_file(self):
        ...

    @input_file.setter
    @abstractmethod
    def input_file(self, file):
        ...

    @property
    @abstractmethod
    def log_file(self):
        ...

    @log_file.setter
    @abstractmethod
    def log_file(self, name):
        ...

    @property
    @abstractmethod
    def parameters_file(self):
        ...

    @parameters_file.setter
    @abstractmethod
    def parameters_file(self, name):
        ...

    @property
    @abstractmethod
    def results_file_name(self):
        ...

    @results_file_name.setter
    @abstractmethod
    def results_file_name(self, name):
        ...

    @property
    @abstractmethod
    def geometry_file_name(self):
        ...

    @geometry_file_name.setter
    @abstractmethod
    def geometry_file_name(self, name):
        ...

    @property
    @abstractmethod
    def application_version(self):
        ...

    @application_version.setter
    @abstractmethod
    def application_version(self, name):
        ...

    @property
    @abstractmethod
    def working_directory_path(self):
        ...

    @working_directory_path.setter
    @abstractmethod
    def working_directory_path(self, name):
        ...


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

