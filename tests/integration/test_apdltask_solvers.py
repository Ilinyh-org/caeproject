import os

import pytest
from pytest_check import check

from caetask import run_threads
from tests.integration.test_caetask.test_apdltask import create_task, solve_task


@pytest.mark.positive
@pytest.mark.solve
@pytest.mark.input_parameters
def test_apdl_multitask_callback(tmpdir):
    input_data = (('1', 1), ('2', 2), ('3', 3), ('4', 4), ('5', 5), ('6', 6), ('7', 7))

    expected_results = (3, 6, 9, 12, 15, 18, 21)

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

    for input_sample, expected_result in zip(input_data, expected_results):
        file_name = "task" + input_sample[0] + "_text_file.dat"
        with check:  # позволяет не прерывать общий процесс при провале assert
            try:
                with open(file_name, "r") as file:
                    actual_result = int(file.readline())
                    assert actual_result == expected_result, f"Error in file {file_name} "
            except FileNotFoundError:
                assert False, f"File {file_name} not found"
