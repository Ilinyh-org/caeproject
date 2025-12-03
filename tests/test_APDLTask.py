import os
from pathlib import Path

import pytest
from pytest_check import check
from caetask import run_processes, run_threads
from caetask import APDLTask
from threading import Lock

lock = Lock()


def setup_method():
    pass


input_data = (('1', 1), ('2', 2), ('3', 3), ('4', 4), ('5', 5), ('6', 6), ('7', 7))


def create_task(index, tempdir=None):  # задаётся пользователем
    global input_data

    task_num = input_data[index][0]
    num_par = input_data[index][1]

    workdir = "temp" + task_num
    os.mkdir(workdir)

    with open(os.path.join(workdir, "test.parm"), "w") as file:
        file.write("num=" + str(num_par))

    task = APDLTask('test' + str(num_par))
    task.input_file = 'test.inp'
    task.parameters_file = os.path.join(workdir, "test.parm")
    if tempdir:
        task.temporary_directory_path = tempdir
    task.memory_size = 64
    task.database_size = 32
    task.results_files_names = [
        "task" + str(num_par) + "_text_file.dat",
        "test" + str(num_par) + "_1.out",
    ]
    return task


def solve_task(task: APDLTask):
    task.solve()


@pytest.mark.positive
@pytest.mark.solve
@pytest.mark.input_parameters
def test_apdl_multitask_callback(tmpdir, capsys):
    global input_data

    EXPECTED_RESULTS = (3, 6, 9, 12, 15, 18, 21)

    os.chdir(tmpdir)

    with open("test.inp", "w") as file:
        file.write("/batch\n")
        file.write("parres,change,test,parm\n")
        file.write("*cfopen,task%num%_text_file,dat\n")
        file.write("*vwrite,num*3\n")
        file.write("%I\n")
        file.write("*cfclos\n")

    tasks = run_threads(create_task, [0, 1, 2, 3, 4, 5, 6])  # список параллельных решаемых задач
    run_threads(solve_task, tasks, max_workers=4)

    for input_sample, expected_result in zip(input_data, EXPECTED_RESULTS):
        file_name = "task" + input_sample[0] + "_text_file.dat"
        with check:  # позволяет не прерывать общий процесс при провале assert
            try:
                with open(file_name, "r") as file:
                    actual_result = int(file.readline())
                    assert actual_result == expected_result, f"Error in file {file_name} "
            except FileNotFoundError:
                assert False, f"File {file_name} not found"


@pytest.fixture(scope="session")
def apdl_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "test.inp"
    with open(fn, "w") as file:
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
def test_apdl_solve(tmpdir, apdl_file, capsys):
    os.chdir(tmpdir)

    EXPECTED_RESULT = "test text from ansys\n"

    task = APDLTask('test')
    task.input_file = apdl_file
    task.results_files_names = ["text_file_from_ansys.dat"]
    task.solve()

    with open("text_file_from_ansys.dat", "r") as file:
        line_from_test_file = file.readline()
    assert line_from_test_file == EXPECTED_RESULT


@pytest.mark.positive
@pytest.mark.solve
def test_apdl_solve_not_in_current_directory(tmp_path: Path, apdl_file, capsys):
    tmpdir1 = tmp_path / "tmpdir1"
    tmpdir1.mkdir()
    tmpdir2 = tmp_path / "tmpdir2"
    tmpdir2.mkdir()
    os.chdir(tmpdir1)

    EXPECTED_RESULT = "test text from ansys\n"

    task = APDLTask('test')
    task.input_file = apdl_file
    task.results_directory_path = tmpdir2
    task.results_files_names = ["text_file_from_ansys.dat"]
    task.solve()

    with open(tmpdir2 / "text_file_from_ansys.dat", "r") as file:
        line_from_test_file = file.readline()
    assert line_from_test_file == EXPECTED_RESULT


@pytest.mark.positive
@pytest.mark.log
def test_apdl_log(tmpdir, apdl_file, capsys):
    os.chdir(tmpdir)

    expected_log_text_parts = [
        "Ansys Mechanical",
        "W E L C O M E   T O   T H E   A N S Y S (R)  P R O G R A M",
        "ANSYS COMMAND LINE ARGUMENTS",
        "A N S Y S   S T A T I S T I C S",
        "ANSYS RUN COMPLETED"]

    task = APDLTask('test')
    task.input_file = apdl_file
    task.log_file = 'test_log_file.log'
    task.results_files_names = ['test_log_file.log']
    task.solve()

    with open("test_log_file.log", "r") as file:
        log_text = file.read()
        for expected_log_text_part in expected_log_text_parts:
            assert expected_log_text_part in log_text


@pytest.fixture(scope="session")
def apdl_file_using_additinal_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "test.inp"
    with open(fn, "w") as file:
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
    fn = tmp_path_factory.mktemp("data") / "additional_text_file.txt"
    with open(fn, "w") as file:
        file.write("3\n7\n4\n")
    return fn


@pytest.mark.positive
@pytest.mark.solve
def test_apdl_solve_additional_text_files(tmpdir, apdl_file_using_additinal_file, additional_text_file, capsys):
    os.chdir(tmpdir)

    EXPECTED_RESULT = "14\n"

    task = APDLTask('test')
    task.input_file = apdl_file_using_additinal_file
    task.additional_text_files = additional_text_file
    task.results_files_names = [
        "text_file_from_ansys.dat",
    ]
    task.solve()

    with open("text_file_from_ansys.dat", "r") as file:
        line_from_test_file = file.readline()
    assert line_from_test_file == EXPECTED_RESULT


@pytest.fixture(scope="session")
def apdl_file_saving_database(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "test1.inp"
    with open(fn, "w") as file:
        file.write("/batch\n")
        file.write("/prep7\n")
        file.write("a=5\n")
        file.write("save,database,db\n")
    return fn


@pytest.fixture(scope="session")
def apdl_file_resuming_database(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "test2.inp"
    with open(fn, "w") as file:
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
def test_apdl_solve_additional_link_files(tmpdir, apdl_file_saving_database, apdl_file_resuming_database, capsys):
    os.chdir(tmpdir)

    EXPECTED_RESULT = "5\n"

    task = APDLTask('test1')
    task.input_file = apdl_file_saving_database
    task.results_files_names = [
        "database.db",
    ]
    task.solve()

    task = APDLTask('test2')
    task.copy_link_files = True
    task.input_file = apdl_file_resuming_database
    task.additional_link_files = [
        "database.db"
    ]
    task.results_files_names = [
        "text_file_from_ansys.dat",
    ]
    task.solve()

    with open("text_file_from_ansys.dat", "r") as file:
        line_from_test_file = file.readline()
    assert line_from_test_file == EXPECTED_RESULT


@pytest.mark.positive
@pytest.mark.solve
def test_apdl_solve_manual_temp_dir(tmpdir, apdl_file, capsys):
    os.chdir(tmpdir)
    MANUAL_TEMP_DIR_NAME = 'solve_dir'
    os.mkdir(MANUAL_TEMP_DIR_NAME)
    EXPECTED_RESULT = "test text from ansys\n"

    task = APDLTask('test')
    task.input_file = apdl_file
    task.temporary_directory_path = os.path.abspath('solve_dir')
    task.results_files_names = ["text_file_from_ansys.dat"]
    task.solve(cleanup=False, delete=False)

    manual_temp_dir_abspath = os.path.abspath(MANUAL_TEMP_DIR_NAME)
    tempdir = next(
        os.path.join(manual_temp_dir_abspath, d)
        for d in os.listdir(manual_temp_dir_abspath)
        if os.path.isdir(os.path.join(manual_temp_dir_abspath, d))
    )

    with open(os.path.join(tempdir, "text_file_from_ansys.dat"), "r") as file:
        line_from_test_file = file.readline()
    assert line_from_test_file == EXPECTED_RESULT


@pytest.mark.positive
@pytest.mark.solve
@pytest.mark.input_parameters
@pytest.mark.parametrize("input_data,expected_result",
                         [(1, 3.14),
                          (10, 31.4)])
def test_apdl_calc_geom_vol(input_data, expected_result, capsys):
    pass


@pytest.mark.positive
@pytest.mark.solve
@pytest.mark.input_parameters
def test_apdl_two_tasks_sum(tmpdir, capsys):
    os.chdir(tmpdir)

    EXPECTED_RESULTS = (3, 6)
    with open("test1.inp", "w") as file:
        file.write("/batch\n")
        file.write("*cfopen,task1_text_file,dat\n")
        file.write("*vwrite,1+2\n")
        file.write("%I\n")
        file.write("*cfclos\n")
    with open("test2.inp", "w") as file:
        file.write("/batch\n")
        file.write("*cfopen,task2_text_file,dat\n")
        file.write("*vwrite,3+3\n")
        file.write("%I\n")
        file.write("*cfclos\n")

    task1 = APDLTask('test1')
    task1.input_file = 'test1.inp'
    task1.results_files_names = ["task1_text_file.dat"]
    task2 = APDLTask('test2')
    task2.input_file = 'test2.inp'
    task2.results_files_names = ["task2_text_file.dat"]

    task1.solve()
    task2.solve()

    with open("task1_text_file.dat", "r") as f:
        actual_result = int(f.readline())
        assert actual_result == EXPECTED_RESULTS[0]
    with open("task2_text_file.dat", "r") as f:
        actual_result = int(f.readline())
        assert actual_result == EXPECTED_RESULTS[1]


@pytest.mark.negative
@pytest.mark.solve
@pytest.mark.error
@pytest.mark.FileNotFoundError
def test_apdl_FileNotFoundError(tmpdir, capsys):
    os.chdir(tmpdir)

    expected_error = FileNotFoundError
    expected_error_message = "some_file.inp не найден"

    with pytest.raises(expected_error) as exc:
        task = APDLTask('test')
        task.input_file = "some_file.inp"
        task.results_files_names = ["text_file_from_ansys.dat"]

        task.solve()
    assert expected_error_message in str(exc.value)


@pytest.mark.negative
@pytest.mark.solve
@pytest.mark.error
@pytest.mark.FileNotFoundError
def test_apdl_results_file_FileNotFoundError(tmpdir, apdl_file, capsys):
    os.chdir(tmpdir)

    expected_error_message = "wrong_file_from_ansys.dat не найден для копирования в "

    task = APDLTask('test')
    task.input_file = apdl_file
    task.results_files_names = ["wrong_file_from_ansys.dat"]

    task.solve()

    actual_error_message = capsys.readouterr().out

    assert expected_error_message in actual_error_message


@pytest.mark.positive
@pytest.mark.solve
def test_apdl__str__(tmpdir, apdl_file, capsys):
    os.chdir(tmpdir)

    EXPECTED_RESULT = 'имя задачи: test\n'\
                      'исполняемый файл: test.inp\n'\
                      'файл логов: test.log\n'\
                      'версия приложения: 212\n'\
                      'количество потоков в задаче: 2\n'\
                      '\n'

    task1 = APDLTask('test')
    task1.input_file = apdl_file
    task1.results_files_names = ["text_file_from_apdl_file.dat"]
    print(task1)
    captured = capsys.readouterr()
    actual_result = captured.out

    assert actual_result == EXPECTED_RESULT


