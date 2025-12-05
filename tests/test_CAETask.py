import os
from pathlib import Path

import pytest
from caetask import APDLTask, FluentTask, CFDPostTask
from caetask.caetask import CAETask
from threading import Lock
import json
from datetime import datetime

lock = Lock()


def setup_method():
    pass


@pytest.fixture(autouse=True)
def reset_counter():
    CAETask.reset()


def parse_iso8601(ts):
    try:
        return datetime.fromisoformat(ts)
    except ValueError as e:
        raise AssertionError(f"Неверный формат ISO 8601: {ts}") from e


@pytest.fixture(scope="session")
def apdl_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "test.inp"
    with open(fn, "w") as file:
        file.write("/batch\n")
    return fn


@pytest.mark.positive
@pytest.mark.solve
@pytest.mark.log
def test_apdl_solve_log(tmpdir, apdl_file, capsys):
    os.chdir(tmpdir)

    LOG_FILE_NAME = "test_APDLTask_solve.log"
    EXPECTED_LOG_FIELDS = {'function_name', 'start_time', 'end_time', 'duration_seconds', 'status'}
    EXPECTED_FUNCTION_NAME = 'solve'
    EXPECTED_STATUS = 'success'

    task = APDLTask('test')
    task.input_file = apdl_file
    task.solve()

    with open(LOG_FILE_NAME, "r", encoding="utf-8") as file:
        data = json.load(file)

        assert set(data.keys()) == EXPECTED_LOG_FIELDS
        assert data['function_name'] == EXPECTED_FUNCTION_NAME
        assert data['status'] == EXPECTED_STATUS

        start_dt = parse_iso8601(data['start_time'])
        end_dt = parse_iso8601(data['end_time'])
        expected_duration = (end_dt - start_dt).total_seconds()
        actual_duration = data['duration_seconds']

        assert abs(actual_duration - expected_duration) < 0.001


@pytest.mark.positive
@pytest.mark.solve
@pytest.mark.log
def test_apdl_solve_log_not_in_current_directory(tmp_path: Path, apdl_file, capsys):
    tmpdir1 = tmp_path / "tmpdir1"
    tmpdir1.mkdir()
    tmpdir2 = tmp_path / "tmpdir2"
    tmpdir2.mkdir()
    os.chdir(tmpdir1)

    LOG_FILE_NAME = "test_APDLTask_solve.log"
    EXPECTED_LOG_FIELDS = {'function_name', 'start_time', 'end_time', 'duration_seconds', 'status'}
    EXPECTED_FUNCTION_NAME = 'solve'
    EXPECTED_STATUS = 'success'

    task = APDLTask('test')
    task.input_file = apdl_file
    task.results_directory_path = tmpdir2
    task.solve()

    with open(tmpdir2 / LOG_FILE_NAME, "r", encoding="utf-8") as file:
        data = json.load(file)

        assert set(data.keys()) == EXPECTED_LOG_FIELDS
        assert data['function_name'] == EXPECTED_FUNCTION_NAME
        assert data['status'] == EXPECTED_STATUS

        start_dt = parse_iso8601(data['start_time'])
        end_dt = parse_iso8601(data['end_time'])
        expected_duration = (end_dt - start_dt).total_seconds()
        actual_duration = data['duration_seconds']

        assert abs(actual_duration - expected_duration) < 0.001


@pytest.mark.positive
@pytest.mark.counter
def test_counter_increment(tmpdir, apdl_file, capsys):
    os.chdir(tmpdir)

    EXPECTED_APDL_TASKS_COUNT = 2
    EXPECTED_FLUENT_TASKS_COUNT = 3

    task1 = APDLTask('test1apdl')
    task2 = APDLTask('test2apdl')
    task3 = FluentTask('test1fluent')
    task4 = FluentTask('test2fluent')
    task5 = FluentTask('test3fluent')

    actual_apdl_tasks_count = APDLTask.count()
    actual_fluent_tasks_count = FluentTask.count()

    assert actual_apdl_tasks_count == EXPECTED_APDL_TASKS_COUNT
    assert actual_fluent_tasks_count == EXPECTED_FLUENT_TASKS_COUNT


@pytest.mark.positive
@pytest.mark.counter
def test_counter_decrement(tmpdir, apdl_file, capsys):
    os.chdir(tmpdir)

    EXPECTED_TASKS_COUNT_BEFORE_DEL = 3
    EXPECTED_TASKS_COUNT_AFTER_DEL = 2

    task1 = CFDPostTask('test1')
    task2 = CFDPostTask('test2')
    task3 = CFDPostTask('test3')
    actual_tasks_count_before_del = CFDPostTask.count()
    del task2
    actual_tasks_count_after_del = CFDPostTask.count()

    assert actual_tasks_count_before_del == EXPECTED_TASKS_COUNT_BEFORE_DEL
    assert actual_tasks_count_after_del == EXPECTED_TASKS_COUNT_AFTER_DEL


@pytest.mark.positive
@pytest.mark.counter
def test_counter_reset_certain_classes(tmpdir, apdl_file, capsys):
    os.chdir(tmpdir)

    EXPECTED_TARGET_TASKS_COUNT_AFTER_RESET = 0
    EXPECTED_OTHER_TASKS_COUNT_AFTER_RESET = 2

    task1 = FluentTask('test1')
    task2 = FluentTask('test2')
    task3 = CFDPostTask('test3')
    task4 = CFDPostTask('test4')
    FluentTask.reset()
    actual_target_tasks_count_after_reset = task1.count()
    actual_other_tasks_count_after_reset = task3.count()

    assert actual_target_tasks_count_after_reset == EXPECTED_TARGET_TASKS_COUNT_AFTER_RESET
    assert actual_other_tasks_count_after_reset == EXPECTED_OTHER_TASKS_COUNT_AFTER_RESET


@pytest.fixture(scope="session")
def scm_simple_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "test.scm"
    with open(fn, "w") as file:
        file.write("(ti-menu-load-string \"exit y\")\n")
    return fn


@pytest.mark.positive
@pytest.mark.solve
@pytest.mark.log
def test_fluent_solve_log(tmpdir, scm_simple_file, capsys):
    os.chdir(tmpdir)

    LOG_FILE_NAME = "test_FluentTask_solve.log"
    EXPECTED_LOG_FIELDS = {'function_name', 'start_time', 'end_time', 'duration_seconds', 'status'}
    EXPECTED_FUNCTION_NAME = 'solve'
    EXPECTED_STATUS = 'success'

    task = FluentTask('test')
    task.input_file = scm_simple_file
    task.solve()

    with open(LOG_FILE_NAME, "r", encoding="utf-8") as file:
        data = json.load(file)

        assert set(data.keys()) == EXPECTED_LOG_FIELDS
        assert data['function_name'] == EXPECTED_FUNCTION_NAME
        assert data['status'] == EXPECTED_STATUS

        start_dt = parse_iso8601(data['start_time'])
        end_dt = parse_iso8601(data['end_time'])
        expected_duration = (end_dt - start_dt).total_seconds()
        actual_duration = data['duration_seconds']

        assert abs(actual_duration - expected_duration) < 0.001


@pytest.mark.negative
@pytest.mark.solve
@pytest.mark.input_parameters
@pytest.mark.log
@pytest.mark.parametrize("raising_exception, expected_status, expected_end_time",
                         [(KeyboardInterrupt, 'running', None),
                          (RuntimeError, 'error', not None)])
def test_apdl_solve_log_with_interrupt(raising_exception, expected_status, expected_end_time,
                                   monkeypatch, tmpdir, apdl_file):
    os.chdir(tmpdir)

    # Создаём класс для подмены объекта Popen объектом с заменённым методом wait
    class FakePopen:
        def __init__(self, *a, **kw):
            pass

        def wait(self):  # прервёт выполнение функции solve
            raise raising_exception

    monkeypatch.setattr("caetask.apdltask.Popen", FakePopen)  # подменяем FakePopen вместо Popen

    LOG_FILE_NAME = "test_APDLTask_solve.log"
    EXPECTED_LOG_FIELDS = {'function_name', 'start_time', 'end_time', 'duration_seconds', 'status'}
    EXPECTED_FUNCTION_NAME = 'solve'

    task = APDLTask('test')
    task.input_file = apdl_file

    with pytest.raises(raising_exception):
        task.solve()

    with open(LOG_FILE_NAME, "r", encoding="utf-8") as file:
        data = json.load(file)

        assert set(data.keys()) == EXPECTED_LOG_FIELDS
        assert data['function_name'] == EXPECTED_FUNCTION_NAME
        assert data['status'].startswith(expected_status)

        parse_iso8601(data['start_time'])  # для проверки формата

        if expected_end_time:  # случай, когда end_time не записался
            parse_iso8601(data['end_time'])  # для проверки формата
        else:  # случай, когда end_time записался
            assert data['end_time'] is None
            assert data['duration_seconds'] is None


@pytest.mark.negative
@pytest.mark.AttributeError
def test_cfdposttask_AttributeError(tmpdir):
    EXPECTED_ERROR = AttributeError
    EXPECTED_ERROR_MESSAGE = "Объект CFDPostTask не поддерживает атрибут temporary_directory_path"

    with pytest.raises(EXPECTED_ERROR) as exc:
        task = CFDPostTask('test')
        task.temporary_directory_path = './'
    assert EXPECTED_ERROR_MESSAGE in str(exc.value)

