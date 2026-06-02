import os

import pytest
from caetask import CFDPostTask
from threading import Lock

lock = Lock()


def setup_method():
    pass


@pytest.fixture(scope="session")
def cse_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "test.cse"
    with open(fn, "w") as file:
        file.write("!my $str = <<END;\n!test text from cfdpost\n!END\n")
        file.write("!open(FH, '>', 'text_file_from_cfdpost.dat') or die $!;\n")
        file.write("!print FH $str;\n")
        file.write("!close(FH);\n")
    return fn


@pytest.mark.positive
@pytest.mark.solve
def test_cfdposttask_start(tmpdir, cse_file, capsys):
    os.chdir(tmpdir)
    expected_result = "test text from cfdpost\n"

    task = CFDPostTask('test')
    task.input_file = cse_file
    task.solve()

    with open("text_file_from_cfdpost.dat", "r") as file:
        line_from_test_file = file.readline()
    assert line_from_test_file == expected_result


@pytest.fixture(scope="session")
def cse_fluentpost_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "test.cse"
    with open(fn, "w") as file:
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
def test_cfdpost_print(tmpdir, cse_fluentpost_file, capsys):
    os.chdir(tmpdir)

    expected_result_base = (
            'имя задачи: test\n' +
            'исполняемый файл: test.cse\n' +
            'файл логов: test.log\n' +
            'версия приложения: 212\n' +
            'путь рабочей директории: ' + str(tmpdir) + '\n\n')

    task1 = CFDPostTask('test')
    task1.input_file = cse_fluentpost_file

    print(task1)

    captured = capsys.readouterr()
    actual_result = captured.out

    assert actual_result == expected_result_base