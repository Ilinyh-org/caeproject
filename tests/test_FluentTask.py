
import pytest
from caetask import FluentTask, APDLTask
import os


def setup_method():
    pass


@pytest.fixture(scope="session")
def scm_simple_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "test.scm"
    with open(fn, "w") as file:
        file.write("(define out (open-output-file \"text_file_from_fluent.dat\"))\n")
        file.write("(display \"test text from fluent\" out)\n")
        file.write("(newline out)\n")
        file.write("(close-output-port out)\n")
        file.write("(ti-menu-load-string \"exit y\")\n")
    return fn


@pytest.fixture(scope="session")
def scm_solve_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "test.scm"
    with open(fn, "w") as file:
        file.write("(define out (open-output-file \"text_file_from_fluent.dat\"))\n")
        file.write("(display \"test text from fluent\" out)\n")
        file.write("(newline out)\n")
        file.write("(close-output-port out)\n")
        file.write("(ti-menu-load-string \"exit y\")\n")
    return fn


@pytest.mark.positive
@pytest.mark.solve
def test_fluent_task_start(tmpdir, scm_simple_file):
    os.chdir(tmpdir)

    expected_result = "test text from fluent\n"

    task1 = FluentTask('test')
    task1.input_file = scm_simple_file
    task1.results_files_names = ["text_file_from_fluent.dat"]
    task1.solve()

    with open("text_file_from_fluent.dat", "r") as file:
        actual_result = file.readline()
    assert actual_result == expected_result


@pytest.mark.positive
@pytest.mark.solve
def test_fluent_task_logs(tmpdir, scm_simple_file):
    os.chdir(tmpdir)

    expected_result = "Welcome to ANSYS Fluent"

    task1 = FluentTask('test')
    task1.input_file = scm_simple_file
    task1.log_file = 'log_test.log'
    task1.results_files_names = [
        "text_file_from_fluent.dat",
        'log_test.log'
    ]
    task1.solve()

    with open("log_test.log", "r") as file:
        assert any(expected_result in line for line in file.readlines())


@pytest.fixture(scope="session")
def inp_mesh_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "mesh.inp"
    with open(fn, "w") as file:
        file.write("/prep7\n")
        file.write("et,1,200,6\n")
        file.write("a1=0.2\n")
        file.write("blc4,,,a1,a1\n")
        file.write("esize,,2\n")
        file.write("amesh,all\n")
        file.write("nsel,s,loc,x\n")
        file.write("cm,inlet,node\n")
        file.write("nsel,s,loc,x,a1\n")
        file.write("cm,outlet,node\n")
        file.write("nsel,s,loc,y\n")
        file.write("nsel,a,loc,y,a1\n")
        file.write("cm,wall,node\n")
        file.write("cm,fluid,elem\n")
        file.write("cdopt,anf\n")
        file.write("cdwrite,comb,mesh,cdb\n")
    return fn


@pytest.fixture(scope="session")
def scm_solve_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "test.scm"
    with open(fn, "w") as file:
        file.write("(ti-menu-load-string \"/file/import/mechanical-apdl/input mesh.cdb\")\n")
        file.write("(ti-menu-load-string \"/solve/iterate 1\")\n")
        file.write("(ti-menu-load-string \"exit y\")\n")
    return fn


@pytest.mark.positive
@pytest.mark.solve
def test_fluent_task_solve(tmpdir, inp_mesh_file, scm_solve_file):
    os.chdir(tmpdir)

    expected_result = "iter  continuity  x-velocity  y-velocity"

    task1 = APDLTask('apdl')
    task1.input_file = inp_mesh_file
    task1.results_files_names = ["mesh.cdb"]
    task1.solve()

    task2 = FluentTask('fluent')
    task2.input_file = scm_solve_file
    task2.log_file = 'log_fluent.log'
    task2.additional_link_files = ['mesh.cdb']
    task2.results_files_names = ["log_fluent.log"]
    task2.solve()

    with open("log_fluent.log", "r") as file:
        assert any(expected_result in line for line in file.readlines())


@pytest.mark.positive
@pytest.mark.solve
def test_fluent_task_return_files_regular_expression(tmpdir, scm_simple_file):
    os.chdir(tmpdir)

    expected_result = "test text from fluent\n"

    task1 = FluentTask('test')
    task1.input_file = scm_simple_file
    task1.results_files_names = ["text_file_*.dat"]
    task1.solve()

    with open("text_file_from_fluent.dat", "r") as file:
        actual_result = file.readline()
    assert actual_result == expected_result


def tearDown() -> None:
    pass


