
import pytest
from pathlib import Path
from caecase import CAECase, Parameter
from caetask import APDLTask
import os

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

