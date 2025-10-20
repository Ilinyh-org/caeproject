import os
import pytest
from pytest_check import check
from caetask import run_processes, run_threads
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
    # os.mkdir('solve_dir')
    expected_result = "test text from cfdpost\n"

    task = CFDPostTask('test')
    task.input_file = cse_file
    # task.results_files_names = ["text_file_from_cfdpost.dat"]
    task.solve()

    with open("text_file_from_cfdpost.dat", "r") as file:
        line_from_test_file = file.readline()
    assert line_from_test_file == expected_result


