"""Integration tests for APDLTask: solving, logs, auxiliary files, temporary
directories, error handling and serialization."""
import os
from pathlib import Path
from threading import Lock

import pytest

from caetask import APDLTask

lock = Lock()


def setup_method():
    """No per-test setup required."""
    pass


@pytest.fixture(scope="session")
def apdl_file(tmp_path_factory):
    """Write an APDL journal writing text into a dat file; return its path."""
    fn = tmp_path_factory.mktemp("data") / "test.inp"
    with open(fn, "w", encoding="utf-8") as file:
        file.write("/batch\n")
        file.write("*dim,text,string,32,1\n")
        file.write("text(1)=\'test text from ansys\'\n")
        file.write("*cfopen,text_file_from_ansys,dat\n")
        file.write("*vwrite,text(1)\n")
        file.write("%C\n")
        file.write("*cfclos\n")
    return fn


@pytest.mark.positive
@pytest.mark.solve
def test_apdl_solve(tmpdir, apdl_file):
    """Verify APDLTask.solve runs the journal and produces the expected text output file."""
    tmpdir.chdir()

    expected_result = "test text from ansys\n"

    task = APDLTask.create_new('test')
    task.input_file = apdl_file
    task.results_files_names = ["text_file_from_ansys.dat"]
    task.solve()

    with open("text_file_from_ansys.dat", "r", encoding="utf-8") as file:
        line_from_test_file = file.readline()
    assert line_from_test_file == expected_result


@pytest.mark.positive
@pytest.mark.solve
def test_apdl_solve_not_in_current_directory(tmp_path: Path, apdl_file):
    """Verify solve places results in the configured results_directory
    outside the current directory."""
    tmpdir1 = tmp_path / "tmpdir1"
    tmpdir1.mkdir()
    tmpdir2 = tmp_path / "tmpdir2"
    tmpdir2.mkdir()
    os.chdir(tmpdir1)

    expected_result = "test text from ansys\n"

    task = APDLTask.create_new('test')
    task.input_file = apdl_file
    task.results_directory = tmpdir2
    task.results_files_names = ["text_file_from_ansys.dat"]
    task.solve()

    with open(tmpdir2 / "text_file_from_ansys.dat", "r", encoding="utf-8") as file:
        line_from_test_file = file.readline()
    assert line_from_test_file == expected_result


@pytest.mark.positive
@pytest.mark.solve
@pytest.mark.log
def test_apdl_log(tmpdir, apdl_file):
    """Verify solve writes a log file containing the expected APDL banner sections."""
    os.chdir(tmpdir)

    expected_log_text_parts = [
        "Ansys Mechanical",
        "W E L C O M E   T O   T H E   A N S Y S (R)  P R O G R A M",
        "ANSYS COMMAND LINE ARGUMENTS",
        "A N S Y S   S T A T I S T I C S",
        "ANSYS RUN COMPLETED"]

    task = APDLTask.create_new('test')
    task.input_file = apdl_file
    task.log_file_name = 'test_log_file.log'
    task.results_files_names = ['test_log_file.log']
    task.solve()

    with open("test_log_file.log", "r", encoding="utf-8") as file:
        log_text = file.read()
        for expected_log_text_part in expected_log_text_parts:
            assert expected_log_text_part in log_text


@pytest.fixture(scope="session")
def apdl_file_using_additional_file(tmp_path_factory):
    """Write an APDL journal reading three numbers from a text file
    and writing their sum; return its path."""
    fn = tmp_path_factory.mktemp("data") / "test.inp"
    with open(fn, "w", encoding="utf-8") as file:
        file.write("/batch\n")
        file.write("*DIM,A,,3\n")
        file.write("*VREAD,A(1),additional_text_file,txt\n")
        file.write("(F1.0)\n")
        file.write("*cfopen,text_file_from_ansys,dat\n")
        file.write("*vwrite,A(1)+A(2)+A(3)\n")
        file.write("%G\n")
        file.write("*cfclos\n")
    return fn


@pytest.fixture(scope="session")
def additional_text_file(tmp_path_factory):
    """Write a text file with three numbers; return its path."""
    fn = tmp_path_factory.mktemp("data") / "additional_text_file.txt"
    with open(fn, "w", encoding="utf-8") as file:
        file.write("3\n7\n4\n")
    return fn


@pytest.mark.positive
@pytest.mark.solve
def test_apdl_solve_additional_text_files(tmpdir, apdl_file_using_additional_file,
                                          additional_text_file):
    """Verify solve reads the additional text file and writes the computed sum."""
    os.chdir(tmpdir)

    expected_result = "14\n"

    task = APDLTask.create_new('test')
    task.input_file = apdl_file_using_additional_file
    task.additional_text_files = additional_text_file
    task.results_files_names = [
        "text_file_from_ansys.dat",
    ]
    task.solve()

    with open("text_file_from_ansys.dat", "r", encoding="utf-8") as file:
        line_from_test_file = file.readline()
    assert line_from_test_file == expected_result


@pytest.fixture(scope="session")
def apdl_file_saving_database(tmp_path_factory):
    """Write an APDL journal saving the database; return its path."""
    fn = tmp_path_factory.mktemp("data") / "test1.inp"
    with open(fn, "w", encoding="utf-8") as file:
        file.write("/batch\n")
        file.write("/prep7\n")
        file.write("a=5\n")
        file.write("save,database,db\n")
    return fn


@pytest.fixture(scope="session")
def apdl_file_resuming_database(tmp_path_factory):
    """Write an APDL journal resuming the database and writing parameter a; return its path."""
    fn = tmp_path_factory.mktemp("data") / "test2.inp"
    with open(fn, "w", encoding="utf-8") as file:
        file.write("/batch\n")
        file.write("/prep7\n")
        file.write("resume,database,db\n")
        file.write("*cfopen,text_file_from_ansys,dat\n")
        file.write("*vwrite,a\n")
        file.write("%I\n")
        file.write("*cfclos\n")
    return fn


@pytest.mark.positive
@pytest.mark.solve
def test_apdl_solve_additional_link_files(tmpdir, apdl_file_saving_database,
                                          apdl_file_resuming_database):
    """Verify a second task can resume the database produced by the first via link files."""
    os.chdir(tmpdir)

    expected_result = "5\n"

    task = APDLTask.create_new('test1')
    task.input_file = apdl_file_saving_database
    task.results_files_names = [
        "database.db",
    ]
    task.solve()

    task = APDLTask.create_new('test2')
    task.copy_link_files = True
    task.input_file = apdl_file_resuming_database
    task.additional_link_files = [
        "database.db"
    ]
    task.results_files_names = [
        "text_file_from_ansys.dat",
    ]
    task.solve()

    with open("text_file_from_ansys.dat", "r", encoding="utf-8") as file:
        line_from_test_file = file.readline()
    assert line_from_test_file == expected_result


@pytest.mark.positive
@pytest.mark.solve
def test_apdl_solve_manual_temp_dir(tmpdir, apdl_file):
    """Verify solve(cleanup=False, delete=False) runs in the given temporary
    directory and keeps results there."""
    os.chdir(tmpdir)
    manual_temp_dir_name = 'solve_dir'
    os.mkdir(manual_temp_dir_name)
    expected_result = "test text from ansys\n"

    task = APDLTask.create_new('test')
    task.input_file = apdl_file
    task.temporary_directory = os.path.abspath('solve_dir')
    task.results_files_names = ["text_file_from_ansys.dat"]
    task.solve(cleanup=False, delete=False)

    manual_temp_dir_abspath = os.path.abspath(manual_temp_dir_name)
    tempdir = next(
        os.path.join(manual_temp_dir_abspath, d)
        for d in os.listdir(manual_temp_dir_abspath)
        if os.path.isdir(os.path.join(manual_temp_dir_abspath, d))
    )

    with open(os.path.join(tempdir, "text_file_from_ansys.dat"), "r", encoding="utf-8") as file:
        line_from_test_file = file.readline()
    assert line_from_test_file == expected_result


@pytest.mark.positive
@pytest.mark.solve
@pytest.mark.input_parameters
@pytest.mark.parametrize("_input_data,_expected_result",
                         [(1, 3.14),
                          (10, 31.4)])
def test_apdl_calc_geom_vol(_input_data, _expected_result):
    """Placeholder: geometry volume calculation is not yet covered."""
    pass


@pytest.mark.positive
@pytest.mark.solve
@pytest.mark.input_parameters
def test_apdl_two_tasks_sum(tmpdir):
    """Verify two sequential APDLTask solves each write their computed sum."""
    os.chdir(tmpdir)

    expected_results = (3, 6)
    with open("test1.inp", "w", encoding="utf-8") as file:
        file.write("/batch\n")
        file.write("*cfopen,task1_text_file,dat\n")
        file.write("*vwrite,1+2\n")
        file.write("%I\n")
        file.write("*cfclos\n")
    with open("test2.inp", "w", encoding="utf-8") as file:
        file.write("/batch\n")
        file.write("*cfopen,task2_text_file,dat\n")
        file.write("*vwrite,3+3\n")
        file.write("%I\n")
        file.write("*cfclos\n")

    task1 = APDLTask.create_new('test1')
    task1.input_file = 'test1.inp'
    task1.results_files_names = ["task1_text_file.dat"]
    task2 = APDLTask.create_new('test2')
    task2.input_file = 'test2.inp'
    task2.results_files_names = ["task2_text_file.dat"]

    task1.solve()
    task2.solve()

    with open("task1_text_file.dat", "r", encoding="utf-8") as f:
        actual_result = int(f.readline())
        assert actual_result == expected_results[0]
    with open("task2_text_file.dat", "r", encoding="utf-8") as f:
        actual_result = int(f.readline())
        assert actual_result == expected_results[1]


@pytest.mark.negative
@pytest.mark.solve
@pytest.mark.error
@pytest.mark.FileNotFoundError
def test_apdl_FileNotFoundError(tmpdir):
    """Verify solving with a missing input file raises FileNotFoundError
    with the expected message."""
    os.chdir(tmpdir)

    expected_error = FileNotFoundError
    expected_error_message = "some_file.inp is not found"

    with pytest.raises(expected_error) as exc:
        task = APDLTask.create_new('test')
        task.input_file = "some_file.inp"
        task.results_files_names = ["text_file_from_ansys.dat"]

        task.solve()
    assert expected_error_message in str(exc.value)


@pytest.mark.negative
@pytest.mark.solve
@pytest.mark.error
@pytest.mark.FileNotFoundError
def test_apdl_results_file_FileNotFoundError(tmpdir, apdl_file, capsys):
    """Verify a missing results file is reported via the expected message on stdout."""
    os.chdir(tmpdir)

    expected_error_message = "wrong_file_from_ansys.dat не найден для копирования в "

    task = APDLTask.create_new('test')
    task.input_file = apdl_file
    task.results_files_names = ["wrong_file_from_ansys.dat"]

    task.solve()

    actual_error_message = capsys.readouterr().out

    assert expected_error_message in actual_error_message


@pytest.mark.positive
@pytest.mark.solve
def test_apdl_print(tmpdir, apdl_file, capsys):
    """Verify print(APDLTask) outputs the task summary in the expected format."""
    os.chdir(tmpdir)

    expected_result = 'имя задачи: test\n'\
                      'исполняемый файл: test.inp\n'\
                      'файл логов: test.log\n'\
                      'версия приложения: 212\n'\
                      'количество потоков в задаче: 2\n'\
                      '\n'

    task1 = APDLTask.create_new('test')
    task1.input_file = apdl_file
    task1.results_files_names = ["text_file_from_apdl_file.dat"]
    print(task1)
    captured = capsys.readouterr()
    actual_result = captured.out

    assert actual_result == expected_result


@pytest.mark.positive
def test_task_to_dict(tmpdir, apdl_file):
    """Verify APDLTask.to_dict serializes all task fields with default values."""
    os.chdir(tmpdir)
    expected_result = {'type': 'apdl',
                       'additional_link_files': None,
                       'additional_text_files': None,
                       'additional_text_files_codes': None,
                       'application_version': '212',
                       'copy_link_files': False,
                       'cores': '2',
                       'database_size': '1024',
                       'geometry_file': '',
                       'memory_size': '2048',
                       'name': 'test',
                       'new_parameter_name': None,
                       'new_parameter_value': None,
                       'parameters_file': None,
                       'results_directory': '.',
                       'results_file_name': None,
                       'results_files_names': ['text_file_from_apdl_file.dat'],
                       'input_file': str(apdl_file),
                       'log_file_name': 'test.log',
                       'status': None}

    task1 = APDLTask.create_new('test')
    task1.input_file = apdl_file
    task1.results_files_names = ["text_file_from_apdl_file.dat"]

    actual_result = task1.to_dict()

    assert actual_result == expected_result


@pytest.mark.positive
def test_task_to_dict_after_solve(tmpdir, apdl_file):
    """Verify to_dict output is unchanged by solving the task."""
    os.chdir(tmpdir)
    expected_result = {'type': 'apdl',
                       'additional_link_files': None,
                       'additional_text_files': None,
                       'additional_text_files_codes': None,
                       'application_version': '212',
                       'copy_link_files': False,
                       'cores': '2',
                       'database_size': '1024',
                       'geometry_file': '',
                       'memory_size': '2048',
                       'name': 'test',
                       'new_parameter_name': None,
                       'new_parameter_value': None,
                       'parameters_file': None,
                       'results_directory': '.',
                       'results_file_name': None,
                       'results_files_names': ['text_file_from_apdl_file.dat'],
                       'input_file': str(apdl_file),
                       'log_file_name': 'test.log',
                       'status': None}

    task1 = APDLTask.create_new('test')
    task1.input_file = apdl_file
    task1.results_files_names = ["text_file_from_apdl_file.dat"]
    task1.solve()

    actual_result = task1.to_dict()

    assert actual_result == expected_result


@pytest.fixture(scope="session")
def apdl_parameters_file(tmp_path_factory):
    """Write an APDL parameters file defining a=5; return its path."""
    fn = tmp_path_factory.mktemp("data") / "test.parm"
    with open(fn, "w", encoding="utf-8") as file:
        file.write("a=5\n")
    return fn


@pytest.fixture(scope="session")
def apdl_parametrized_file(tmp_path_factory):
    """Write an APDL journal reading the parameters file
    and writing parameter a; return its path."""
    fn = tmp_path_factory.mktemp("data") / "test.inp"
    with open(fn, "w", encoding="utf-8") as file:
        file.write("/batch\n")
        file.write("parres,new,test,parm\n")
        file.write("*cfopen,text_file_from_ansys,dat\n")
        file.write("*vwrite,a\n")
        file.write("%G\n")
        file.write("*cfclos\n")
    return fn


@pytest.mark.positive
@pytest.mark.solve
def test_apdl_parameters_file(tmpdir, apdl_parametrized_file, apdl_parameters_file):
    """Verify solve loads the parameters file and the journal reads the parameter value."""
    os.chdir(tmpdir)

    expected_result = "5\n"

    task = APDLTask.create_new('test')
    task.parameters_file = apdl_parameters_file
    task.input_file = apdl_parametrized_file
    task.results_files_names = ["text_file_from_ansys.dat"]
    task.solve()

    with open("text_file_from_ansys.dat", "r", encoding="utf-8") as file:
        line_from_test_file = file.readline()
    assert line_from_test_file == expected_result
