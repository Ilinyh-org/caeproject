
import pytest
from caetask import FluentTask, APDLTask
import os
import glob


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


@pytest.mark.positive
@pytest.mark.solve
def test_fluent_task_start(tmpdir, scm_simple_file):
    os.chdir(tmpdir)

    EXPECTED_RESULT = "test text from fluent\n"

    task1 = FluentTask('test')
    task1.input_file = scm_simple_file
    task1.results_files_names = ["text_file_from_fluent.dat"]
    task1.solve()

    with open("text_file_from_fluent.dat", "r") as file:
        actual_result = file.readline()
    assert actual_result == EXPECTED_RESULT


@pytest.fixture(scope="session")
def scm_parm_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "test_parm.scm"
    with open(fn, "w") as file:
        file.write("(define A1 0.01)\n")
        file.write("(define B1 2)\n")
        file.write("(define C1 \"text\")\n")
    return fn


@pytest.fixture(scope="session")
def scm_use_parm_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "test.scm"
    with open(fn, "w") as file:
        file.write("(define out (open-output-file \"text_file_from_fluent.dat\"))\n")
        file.write("(if (file-exists? \"test_parm.scm\")\n")
        file.write("    (load \"test_parm.scm\")\n")
        file.write("    #f)\n")
        file.write("(write A1 out)\n")
        file.write("(newline out)\n")
        file.write("(write B1 out)\n")
        file.write("(newline out)\n")
        file.write("(write C1 out)\n")
        file.write("(newline out)\n")
        file.write("(close-output-port out)\n")
        file.write("(ti-menu-load-string \"exit y\")\n")
    return fn


@pytest.mark.positive
@pytest.mark.solve
def test_fluent_task_parameters_file(tmpdir, scm_use_parm_file, scm_parm_file):
    os.chdir(tmpdir)

    EXPECTED_RESULT = ["0.01\n", "2\n", "\"text\"\n"]

    task1 = FluentTask('test')
    task1.input_file = scm_use_parm_file
    task1.parameters_file = scm_parm_file
    task1.results_files_names = ["text_file_from_fluent.dat"]
    task1.solve()

    with open("text_file_from_fluent.dat", "r") as file:
        actual_result = file.readlines()
    assert actual_result == EXPECTED_RESULT


@pytest.mark.positive
@pytest.mark.solve
def test_fluent_task_logs(tmpdir, scm_simple_file):
    os.chdir(tmpdir)

    EXPECTED_RESULT = "Welcome to ANSYS Fluent"

    task1 = FluentTask('test')
    task1.input_file = scm_simple_file
    task1.log_file = 'log_test.log'
    task1.results_files_names = [
        "text_file_from_fluent.dat",
        'log_test.log'
    ]
    task1.solve()

    with open("log_test.log", "r") as file:
        assert any(EXPECTED_RESULT in line for line in file.readlines())


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

    EXPECTED_RESULT = "iter  continuity  x-velocity  y-velocity"

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
        assert any(EXPECTED_RESULT in line for line in file.readlines())


@pytest.mark.negative
@pytest.mark.solve
def test_fluent_task_solve_wrong_dimension(tmpdir, inp_mesh_file, scm_solve_file):
    os.chdir(tmpdir)

    expected_error = PermissionError

    task1 = APDLTask('apdl')
    task1.input_file = inp_mesh_file
    task1.results_files_names = ["mesh.cdb"]
    task1.solve()

    task2 = FluentTask('fluent')
    task2.input_file = scm_solve_file
    task2.log_file = 'log_fluent.log'
    task2.additional_link_files = ['mesh.cdb']
    task2.results_files_names = ["log_fluent.log"]
    task2.dimension = "3d"

    with pytest.raises(expected_error):
        task2.solve()


@pytest.fixture(scope="session")
def scm_transient_solve_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "test.scm"
    with open(fn, "w") as file:
        file.write("(ti-menu-load-string \"/file/import/mechanical-apdl/input mesh.cdb\")\n")
        file.write("(ti-menu-load-string \"/define/models/unsteady-1st-order? yes\")\n")
        file.write("(ti-menu-load-string \"/file/auto-save/data-frequency 1\")\n")
        file.write("(ti-menu-load-string \"/file/auto-save/case-frequency each-time\")\n")
        file.write("(ti-menu-load-string \"/file/auto-save/append-file-name-with flow-time 6\")\n")
        file.write("(ti-menu-load-string \"/file/auto-save/root-name results\")\n")
        file.write("(ti-menu-load-string \"/solve/initialize/initialize-flow\")\n")
        file.write("(ti-menu-load-string \"/solve/dual-time-iterate 5 10\")\n")
        file.write("(ti-menu-load-string \"exit y\")\n")
    return fn


@pytest.mark.positive
@pytest.mark.solve
def test_cfdposttask_transient_get_csv_results(tmpdir, inp_mesh_file, scm_transient_solve_file, capsys):
    os.chdir(tmpdir)
    EXPECTED_RESULTS = {"dat_files_number": 5,
                        "cas_files_number": 5,
                        "flprj_files_number": 1}

    task1 = APDLTask('apdl')
    task1.input_file = inp_mesh_file
    task1.results_files_names = ["mesh.cdb"]
    task1.solve()

    task2 = FluentTask('fluent')
    task2.input_file = scm_transient_solve_file
    task2.log_file = 'log_fluent.log'
    task2.additional_link_files = ['mesh.cdb']
    task2.results_files_names = ["log_fluent.log", "results*"]
    task2.solve()

    dat_files_number = len(glob.glob("results*.dat.h5"))
    cas_files_number = len(glob.glob("results*.cas.h5"))
    flprj_files_number = len(glob.glob("results.flprj"))

    assert dat_files_number == EXPECTED_RESULTS["dat_files_number"]
    assert cas_files_number == EXPECTED_RESULTS["cas_files_number"]
    assert flprj_files_number == EXPECTED_RESULTS["flprj_files_number"]


@pytest.mark.positive
@pytest.mark.solve
def test_fluent_task_return_files_regular_expression(tmpdir, scm_simple_file):
    os.chdir(tmpdir)

    EXPECTED_RESULT = "test text from fluent\n"

    task1 = FluentTask('test')
    task1.input_file = scm_simple_file
    task1.results_files_names = ["text_file_*.dat"]
    task1.solve()

    with open("text_file_from_fluent.dat", "r") as file:
        actual_result = file.readline()
    assert actual_result == EXPECTED_RESULT


@pytest.mark.positive
@pytest.mark.solve
def test_fluent__str__(tmpdir, scm_simple_file, capsys):
    os.chdir(tmpdir)

    EXPECTED_RESULT = 'имя задачи: test\n'\
                      'исполняемый файл: test.scm\n'\
                      'файл логов: test.log\n'\
                      'версия приложения: 212\n'\
                      'количество потоков в задаче: 2\n'\
                      '\n'

    task1 = FluentTask('test')
    task1.input_file = scm_simple_file
    task1.results_files_names = ["text_file_from_fluent.dat"]
    print(task1)
    captured = capsys.readouterr()
    actual_result = captured.out

    assert actual_result == EXPECTED_RESULT


def tearDown() -> None:
    pass


