"""Integration test for creating and solving several APDLTask instances via run_threads."""
from pathlib import Path

import pytest
from pytest_check import check

from caetask import APDLTask, run_threads


def create_task(index, tempdir=None):  # задаётся пользователем
    """Build an APDLTask from a (task_num, num_par) index
    with its own workdir and parameters file."""
    task_num = index[0]
    num_par = index[1]

    workdir = Path.cwd() / f"temp{task_num}" # + task_num
    workdir.mkdir()

    with open(workdir / "test.parm", "w", encoding="utf-8") as file:
        file.write("num=" + str(num_par))

    task = APDLTask.create_new(f'test{num_par}')
    task.input_file = 'test.inp'
    task.parameters_file = workdir / "test.parm"
    if tempdir:
        task.temporary_directory = tempdir
    task.memory_size = 64
    task.database_size = 32
    task.results_files_names = [
        f"task{num_par}_text_file.dat",
        f"test{num_par}_1.out",
    ]
    return task


def solve_task(task: APDLTask):
    """Solve the given APDLTask."""
    task.solve()


@pytest.mark.positive
@pytest.mark.solve
@pytest.mark.input_parameters
@pytest.mark.external
def test_apdl_multitask_callback(tmpdir):
    """Verify threaded tasks each compute num*3 from their parameters file
    into the expected results file."""
    input_data = (('1', 1), ('2', 2), ('3', 3), ('4', 4), ('5', 5), ('6', 6), ('7', 7))

    expected_results = (3, 6, 9, 12, 15, 18, 21)

    tmpdir.chdir()

    with open("test.inp", "w", encoding="utf-8") as file:
        file.write("/batch\n")
        file.write("parres,change,test,parm\n")
        file.write("*cfopen,task%num%_text_file,dat\n")
        file.write("*vwrite,num*3\n")
        file.write("%I\n")
        file.write("*cfclos\n")

    tasks = run_threads(create_task, input_data)  # список параллельных решаемых задач
    run_threads(solve_task, tasks, max_workers=4)

    for input_sample, expected_result in zip(input_data, expected_results):
        file_name = f"task{input_sample[0]}_text_file.dat"
        # позволяет не прерывать общий процесс при провале assert
        with (check,
              open(file_name, "r", encoding="utf-8") as file):
            # try:
            actual_result = int(file.readline())
            assert actual_result == expected_result, f"Error in file {file_name}"
            # except FileNotFoundError:
            #     assert False, f"File {file_name} not found"
