"""Integration tests for CFDPostTask: execution, string representation and serialization."""
import os
from threading import Lock

import pytest

from caetask import CFDPostTask

lock = Lock()


def setup_method():
    """No per-test setup required."""


@pytest.fixture(scope="session")
def cse_file(tmp_path_factory):
    """Write a CFD-Post session file writing text into a dat file; return its path."""
    fn = tmp_path_factory.mktemp("data") / "test.cse"
    with open(fn, "w", encoding="utf-8") as file:
        file.write("!my $str = <<END;\n!test text from cfdpost\n!END\n")
        file.write("!open(FH, '>', 'text_file_from_cfdpost.dat') or die $!;\n")
        file.write("!print FH $str;\n")
        file.write("!close(FH);\n")
    return fn


@pytest.mark.positive
@pytest.mark.solve
def test_cfdposttask_start(tmpdir, cse_file):
    """Verify CFDPostTask.solve runs the session file and writes the expected text output."""
    os.chdir(tmpdir)
    expected_result = "test text from cfdpost\n"

    task = CFDPostTask.create_new('test')
    task.input_file = cse_file
    task.solve()

    with open("text_file_from_cfdpost.dat", "r", encoding="utf-8") as file:
        line_from_test_file = file.readline()
    assert line_from_test_file == expected_result


@pytest.fixture(scope="session")
def cse_cfdpost_file(tmp_path_factory):
    """Write a CFD-Post session file exporting inlet velocity to CSV; return its path."""
    fn = tmp_path_factory.mktemp("data") / "test.cse"
    with open(fn, "w", encoding="utf-8") as file:
        file.write(">load filename=results.cas.h5, force_reload=true\n")
        file.write("EXPORT:\n")
        file.write("  CSV Type = CSV\n")
        file.write("  Export File = export.csv\n")
        file.write("  Export Geometry = Off\n")
        file.write("  Include File Information = Off\n")
        file.write("  Include Header = Off\n")
        file.write("  Location = inlet\n")
        file.write("  Location List = inlet\n")
        file.write("  Overwrite = On\n")
        file.write("  Precision = 2\n")
        file.write('  Separator = ", "\n')
        file.write("  Variable List = Velocity u\n")
        file.write("END\n")
        file.write(">export\n")
    return fn


@pytest.mark.positive
@pytest.mark.solve
def test_cfdpost_print(tmpdir, cse_cfdpost_file, capsys):
    """Verify print(CFDPostTask) outputs the task summary in the expected format."""
    os.chdir(tmpdir)

    expected_result_base = (
            'имя задачи: test\n' +
            'исполняемый файл: test.cse\n' +
            'файл логов: test.log\n' +
            'версия приложения: 212\n' +
            'путь рабочей директории: ' + str(tmpdir) + '\n\n')

    task1 = CFDPostTask.create_new('test')
    task1.input_file = cse_cfdpost_file

    print(task1)

    captured = capsys.readouterr()
    actual_result = captured.out

    assert actual_result == expected_result_base



@pytest.mark.positive
def test_task_to_dict(tmpdir, cse_cfdpost_file):
    """Verify CFDPostTask.to_dict serializes all task fields with their values."""
    os.chdir(tmpdir)
    expected_result = {'additional_link_files': None,
                       'type': 'cfdpost',
                       'application_version': '212',
                       'name': 'test',
                       'working_directory': str(tmpdir),
                       'parameters_file': None,
                       'results_directory': '.',
                       'results_files_names': ['text_file_from_fluent.dat'],
                       'input_file': str(cse_cfdpost_file),
                       'log_file_name': 'test.log',
                       }

    task1 = CFDPostTask.create_new('test')
    task1.input_file = cse_cfdpost_file
    task1.results_files_names = ["text_file_from_fluent.dat"]

    actual_result = task1.to_dict()

    assert actual_result == expected_result
