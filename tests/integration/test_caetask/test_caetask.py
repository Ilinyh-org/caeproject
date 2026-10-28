"""Integration tests for CAETask logging, per-class task counters and file loading."""
from datetime import datetime
import json
import os
from pathlib import Path
from threading import Lock

import pytest

from caetask import APDLTask, FluentTask, CFDPostTask
from caetask import CAETask

lock = Lock()


def setup_method():
    """No per-test setup required."""
    pass


@pytest.fixture(autouse=True)
def reset_counter():
    """Reset the CAETask counter before each test."""
    CAETask.reset()


def parse_iso8601(ts):
    """Parse an ISO 8601 timestamp, failing the test on a bad format."""
    try:
        return datetime.fromisoformat(ts)
    except ValueError as e:
        raise AssertionError(f"Неверный формат ISO 8601: {ts}") from e


@pytest.fixture(scope="session")
def apdl_file(tmp_path_factory):
    """Write a minimal APDL journal; return its path."""
    fn = tmp_path_factory.mktemp("data") / "test.inp"
    with open(fn, "w", encoding="utf-8") as file:
        file.write("/batch\n")
    return fn


@pytest.fixture(scope="session")
def apdl_parameters_file(tmp_path_factory):
    """Write an APDL parameters file with a=1 and b=-2.4; return its path."""
    fn = tmp_path_factory.mktemp("data") / "test.parm"
    with open(fn, "w", encoding="utf-8") as file:
        file.write("a=1\n")
        file.write("b=-2.4\n")
    return fn


@pytest.mark.positive
@pytest.mark.solve
@pytest.mark.log
def test_apdl_solve_log(tmpdir, apdl_file):
    """Verify APDLTask.solve writes a JSON log with the expected fields,
    status and consistent duration."""
    os.chdir(tmpdir)

    log_file_name = "test_APDLTask_solve.log"
    expected_log_fields = {'function_name', 'start_time', 'end_time', 'duration_seconds', 'status'}
    expected_function_name = 'solve'
    expected_status = 'success'

    task = APDLTask.create_new('test')
    task.input_file = apdl_file
    task.solve()

    with open(log_file_name, "r", encoding="utf-8") as file:
        data = json.load(file)

        assert set(data.keys()) == expected_log_fields
        assert data['function_name'] == expected_function_name
        assert data['status'] == expected_status

        start_dt = parse_iso8601(data['start_time'])
        end_dt = parse_iso8601(data['end_time'])
        expected_duration = (end_dt - start_dt).total_seconds()
        actual_duration = data['duration_seconds']

        assert abs(actual_duration - expected_duration) < 0.001


@pytest.mark.positive
@pytest.mark.solve
@pytest.mark.log
def test_apdl_solve_log_not_in_current_directory(tmp_path: Path, apdl_file):
    """Verify the solve log is written to the configured results_directory."""
    tmpdir1 = tmp_path / "tmpdir1"
    tmpdir1.mkdir()
    tmpdir2 = tmp_path / "tmpdir2"
    tmpdir2.mkdir()
    os.chdir(tmpdir1)

    log_file_name = "test_APDLTask_solve.log"
    expected_log_fields = {'function_name', 'start_time', 'end_time', 'duration_seconds', 'status'}
    expected_function_name = 'solve'
    expected_status = 'success'

    task = APDLTask.create_new('test')
    task.input_file = apdl_file
    task.results_directory = tmpdir2
    task.solve()

    with open(tmpdir2 / log_file_name, "r", encoding="utf-8") as file:
        data = json.load(file)

        assert set(data.keys()) == expected_log_fields
        assert data['function_name'] == expected_function_name
        assert data['status'] == expected_status

        start_dt = parse_iso8601(data['start_time'])
        end_dt = parse_iso8601(data['end_time'])
        expected_duration = (end_dt - start_dt).total_seconds()
        actual_duration = data['duration_seconds']

        assert abs(actual_duration - expected_duration) < 0.001


@pytest.mark.positive
@pytest.mark.counter
def test_counter_increment(tmpdir):
    """Verify per-class counters increment independently for APDLTask and FluentTask."""
    os.chdir(tmpdir)

    expected_apdl_tasks_count = 2
    expected_fluent_tasks_count = 3

    task1 = APDLTask.create_new('test1apdl')
    task2 = APDLTask.create_new('test2apdl')
    task3 = FluentTask('test1fluent')
    task4 = FluentTask('test2fluent')
    task5 = FluentTask('test3fluent')

    actual_apdl_tasks_count = APDLTask.count()
    actual_fluent_tasks_count = FluentTask.count()

    assert actual_apdl_tasks_count == expected_apdl_tasks_count
    assert actual_fluent_tasks_count == expected_fluent_tasks_count


@pytest.mark.positive
@pytest.mark.counter
def test_counter_decrement(tmpdir):
    """Verify deleting a task decrements its class counter."""
    os.chdir(tmpdir)

    expected_tasks_count_before_del = 3
    expected_tasks_count_after_del = 2

    task1 = CFDPostTask('test1')
    task2 = CFDPostTask('test2')
    task3 = CFDPostTask('test3')
    actual_tasks_count_before_del = CFDPostTask.count()
    del task2
    actual_tasks_count_after_del = CFDPostTask.count()

    assert actual_tasks_count_before_del == expected_tasks_count_before_del
    assert actual_tasks_count_after_del == expected_tasks_count_after_del


@pytest.mark.positive
@pytest.mark.counter
def test_counter_reset_certain_classes(tmpdir):
    """Verify reset() zeroes only the target class counter, leaving others intact."""
    os.chdir(tmpdir)

    expected_target_tasks_count_after_reset = 0
    expected_other_tasks_count_after_reset = 2

    task1 = FluentTask('test1')
    task2 = FluentTask('test2')
    task3 = CFDPostTask('test3')
    task4 = CFDPostTask('test4')
    FluentTask.reset()
    actual_target_tasks_count_after_reset = task1.count()
    actual_other_tasks_count_after_reset = task3.count()

    assert actual_target_tasks_count_after_reset == expected_target_tasks_count_after_reset
    assert actual_other_tasks_count_after_reset == expected_other_tasks_count_after_reset


@pytest.fixture(scope="session")
def scm_simple_file(tmp_path_factory):
    """Write a Fluent journal that just exits; return its path."""
    fn = tmp_path_factory.mktemp("data") / "test.scm"
    with open(fn, "w", encoding="utf-8") as file:
        file.write("(ti-menu-load-string \"exit y\")\n")
    return fn


@pytest.mark.positive
@pytest.mark.solve
@pytest.mark.log
def test_fluent_solve_log(tmpdir, scm_simple_file):
    """Verify FluentTask.solve writes a JSON log with the expected fields and duration."""
    tmpdir.chdir()

    log_file_name = "test_FluentTask_solve.log"
    expected_log_fields = {'function_name', 'start_time', 'end_time', 'duration_seconds', 'status'}
    expected_function_name = 'solve'
    expected_status = 'success'

    task = FluentTask.create_new('test')
    task.input_file = scm_simple_file
    task.solve()

    with open(log_file_name, "r", encoding="utf-8") as file:
        data = json.load(file)

        assert set(data.keys()) == expected_log_fields
        assert data['function_name'] == expected_function_name
        assert data['status'] == expected_status

        start_dt = parse_iso8601(data['start_time'])
        end_dt = parse_iso8601(data['end_time'])
        expected_duration = (end_dt - start_dt).total_seconds()
        actual_duration = data['duration_seconds']

        assert actual_duration == pytest.approx(expected_duration, 1E-3)


# Создаём класс для подмены объекта Popen объектом с заменённым методом wait
class FakePopen:
    """Stub replacing Popen whose wait() raises the parametrized exception."""

    def __init__(self, raising_exception, *a, **kw):
        """Accept any arguments; no initialization required."""
        self._exc = raising_exception

    def wait(self):  # прервёт выполнение функции solve
        """Raise the parametrized exception to interrupt solve."""
        raise self._exc

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.fixture
def fake_popen(monkeypatch):
    """Patch Popen in the module under test; returns a setter for the exception.

    Usage:
        def test_solve_timeout(fake_popen):
            fake_popen(TimeoutError("boom"))
            with pytest.raises(TimeoutError):
                solve(...)
    """
    def _install(exc, target="caetask.apdltask.Popen"):
        monkeypatch.setattr(
            target,
            lambda *a, **kw: FakePopen(exc, *a, **kw),
        )
        return exc

    return _install


@pytest.mark.negative
@pytest.mark.solve
@pytest.mark.input_parameters
@pytest.mark.log
@pytest.mark.parametrize(
    "raising_exception, expected_status, expected_end_time",
    [
        (KeyboardInterrupt, 'running', None),
        (RuntimeError, 'error', not None)
    ],
)
def test_apdl_solve_log_with_interrupt(
        raising_exception, expected_status, expected_end_time,
        monkeypatch, tmpdir, apdl_file, fake_popen):
    """Verify interrupts during solve log status 'running' (no end time)
    or 'error' (with end time)."""
    os.chdir(tmpdir)

    fake_popen(raising_exception)   # target defaults to caetask.apdltask.Popen

    log_file_name = "test_APDLTask_solve.log"
    expected_log_fields = {'function_name', 'start_time', 'end_time', 'duration_seconds', 'status'}
    expected_function_name = 'solve'

    task = APDLTask.create_new('test')
    task.input_file = apdl_file

    with pytest.raises(raising_exception):
        task.solve()

    with open(log_file_name, "r", encoding="utf-8") as file:
        data = json.load(file)

        assert set(data.keys()) == expected_log_fields
        assert data['function_name'] == expected_function_name
        assert data['status'].startswith(expected_status)

        parse_iso8601(data['start_time'])  # для проверки формата

        if expected_end_time:  # случай, когда end_time не записался
            parse_iso8601(data['end_time'])  # для проверки формата
        else:  # случай, когда end_time записался
            assert data['end_time'] is None
            assert data['duration_seconds'] is None


@pytest.mark.negative
@pytest.mark.solve
@pytest.mark.input_parameters
@pytest.mark.log
@pytest.mark.parametrize("raising_exception, expected_status, expected_end_time",
                         [(KeyboardInterrupt, 'running', None),
                          (RuntimeError, 'error', not None)])
def test_apdl_solve_log_with_interrupt_not_in_current_directory(
        raising_exception, expected_status,
        expected_end_time, monkeypatch,
        tmp_path: Path, apdl_file, fake_popen):
    """Verify interrupt logging also works with results_directory outside the current directory."""
    tmpdir1 = tmp_path / "tmpdir1"
    tmpdir1.mkdir()
    tmpdir2 = tmp_path / "tmpdir2"
    tmpdir2.mkdir()
    os.chdir(tmpdir1)

    fake_popen(raising_exception)   # target defaults to caetask.apdltask.Popen

    log_file_name = "test_APDLTask_solve.log"
    expected_log_fields = {'function_name', 'start_time', 'end_time', 'duration_seconds', 'status'}
    expected_function_name = 'solve'

    task = APDLTask.create_new('test')
    task.input_file = apdl_file
    task.results_directory = tmpdir2

    with pytest.raises(raising_exception):
        task.solve()

    with open(tmpdir2 / log_file_name, "r", encoding="utf-8") as file:
        data = json.load(file)

        assert set(data.keys()) == expected_log_fields
        assert data['function_name'] == expected_function_name
        assert data['status'].startswith(expected_status)

        parse_iso8601(data['start_time'])  # для проверки формата

        if expected_end_time:  # случай, когда end_time не записался
            parse_iso8601(data['end_time'])  # для проверки формата
        else:  # случай, когда end_time записался
            assert data['end_time'] is None
            assert data['duration_seconds'] is None


@pytest.mark.positive
def test_load_inputs_input_file(apdl_file):
    """Verify load_files reads the input file code into _input_file_code."""
    expected_input_file_code = ["/batch\n"]

    task = APDLTask.create_new('test')
    task.input_file = apdl_file
    task.load_files()

    actual_input_file_code = task._input_file_code

    assert actual_input_file_code == expected_input_file_code


@pytest.mark.positive
def test_load_inputs_parameters_file(apdl_parameters_file):
    """Verify load_files reads the parameters file code into _parameters_file_code."""
    expected_parameters_file_code = ["a=1\n", "b=-2.4\n"]

    task = APDLTask.create_new('test')
    task.parameters_file = apdl_parameters_file
    task.load_files()

    actual_parameters_file_code = task._parameters_file_code

    assert actual_parameters_file_code == expected_parameters_file_code


@pytest.mark.negative
def test_load_inputs_input_file_FileNotFoundError():
    """Verify load_files raises FileNotFoundError with the full path for a missing input file."""
    expected_error = FileNotFoundError
    expected_error_message = str(Path.cwd() / "test.inp") + " is not found"

    task = APDLTask.create_new('test')
    task.input_file = "test.inp"

    with pytest.raises(expected_error) as exc:
        task.load_files()

    assert expected_error_message in str(exc.value)


@pytest.mark.negative
def test_load_inputs_parameters_file_FileNotFoundError():
    """Verify load_files raises FileNotFoundError with the full path
    for a missing parameters file."""
    expected_error = FileNotFoundError
    expected_error_message = str(Path.cwd() / "test.parm") + " is not found"

    task = APDLTask.create_new('test')
    task.parameters_file = "test.parm"

    with pytest.raises(expected_error) as exc:
        task.load_files()

    assert expected_error_message in str(exc.value)
