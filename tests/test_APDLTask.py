import os
import pytest
from caetask import run_processes, run_threads
from caetask import APDLTask
from threading import Lock

lock = Lock()


def setup_method():
    pass


input_data = (('1', 1), ('2', 2), ('3', 3), ('4', 4), ('5', 5))


def create_task(index):  # задаётся пользователем
    global input_data

    task_num = input_data[index][0]
    num_par = input_data[index][1]

    tempdir = "temp" + task_num
    os.mkdir(tempdir)

    with open(os.path.join(tempdir, "test.parm"), "w") as file:
        file.write("num=" + str(num_par))

    task = APDLTask('test')
    task.input_file = 'test.inp'
    task.parameters_file = os.path.join(tempdir, "test.parm")
    task.results_files_names = ["task" + str(num_par) + "_text_file.dat"]
    return task


def solve_task(task: APDLTask):
    task.solve()


@pytest.mark.positive
@pytest.mark.solve
@pytest.mark.input_parameters
def test_apdl_multitask_prod(tmpdir, capsys):
    expected_results = (3, 6)

    os.chdir(tmpdir)

    with open("test.inp", "w") as file:
        file.write("/batch\n")
        file.write("parres,change,test,parm\n")
        file.write("*cfopen,task%num%_text_file,dat\n")
        file.write("*vwrite,num*3\n")
        file.write("%I\n")
        file.write("*cfclos\n")

    tasks = run_processes(create_task, [0, 1])  # список параллельных решаемых задач
    run_threads(solve_task, tasks)

    for input_sample, expected_result in zip(input_data, expected_results):
        with open("task" + input_sample[0] + "_text_file.dat", "r") as file:
            actual_result = int(file.readline())
        assert actual_result == expected_result


# class TestAPDLTask:
# global lock, completed, total_tasks

@pytest.mark.positive
@pytest.mark.solve
@pytest.mark.input_parameters
def test_apdl_multitask_callback(tmpdir, capsys):
    global input_data

    expected_results = (3, 6, 9, 12, 15)

    os.chdir(tmpdir)

    with open("test.inp", "w") as file:
        file.write("/batch\n")
        file.write("parres,change,test,parm\n")
        file.write("*cfopen,task%num%_text_file,dat\n")
        file.write("*vwrite,num*3\n")
        file.write("%I\n")
        file.write("*cfclos\n")

    tasks = run_threads(create_task, [0, 1, 2, 3, 4], max_workers=2)  # список параллельных решаемых задач
    run_threads(solve_task, tasks, max_workers=2)

    for input_sample, expected_result in zip(input_data, expected_results):
        with open("task" + input_sample[0] + "_text_file.dat", "r") as file:
            actual_result = int(file.readline())
        assert actual_result == expected_result


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

    expected_result = "test text from ansys\n"

    task = APDLTask('test')
    task.input_file = apdl_file
    task.results_files_names = ["text_file_from_ansys.dat"]
    task.solve()

    with open("text_file_from_ansys.dat", "r") as file:
        line_from_test_file = file.readline()
    assert line_from_test_file == expected_result


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

    expected_results = (3, 6)
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
        assert actual_result == expected_results[0]
    with open("task2_text_file.dat", "r") as f:
        actual_result = int(f.readline())
        assert actual_result == expected_results[1]


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

    expected_error = FileNotFoundError
    expected_error_message = "wrong_file_from_ansys.dat не найден для копирования в "

    with pytest.raises(expected_error) as exc:
        task = APDLTask('test')
        task.input_file = apdl_file
        task.results_files_names = ["wrong_file_from_ansys.dat"]

        task.solve()
    assert expected_error_message in str(exc.value)
