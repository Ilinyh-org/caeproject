import os
import pytest
from caetask import APDLTask, FluentTask
from threading import Lock
import json
from datetime import datetime

lock = Lock()


def setup_method():
    pass


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
def test_apdl_solve(tmpdir, apdl_file, capsys):
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


@pytest.fixture(scope="session")
def scm_simple_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "test.scm"
    with open(fn, "w") as file:
        file.write("(ti-menu-load-string \"exit y\")\n")
    return fn


@pytest.mark.positive
@pytest.mark.solve
def test_fluent_solve(tmpdir, scm_simple_file, capsys):
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
@pytest.mark.parametrize("raising_exception, expected_status, expected_end_time",
                         [(KeyboardInterrupt, 'running', None),
                          (RuntimeError, 'error', not None)])
def test_apdl_solve_with_interrupt(raising_exception, expected_status, expected_end_time,
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
