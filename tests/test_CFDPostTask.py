import os
import pytest
from pytest_check import check
from caetask import run_processes, run_threads, APDLTask, FluentTask
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
        file.write("(ti-menu-load-string \"/file/write-case results.cas.h5\")\n")
        file.write("(ti-menu-load-string \"/file/write-data results.dat.h5\")\n")
        file.write("(ti-menu-load-string \"exit y\")\n")
    return fn


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
def test_cfdposttask_get_csv_results(tmpdir, inp_mesh_file, scm_solve_file, cse_fluentpost_file, capsys):
    os.chdir(tmpdir)
    expected_result = 6

    task1 = APDLTask('apdl')
    task1.input_file = inp_mesh_file
    task1.results_files_names = ["mesh.cdb"]
    task1.solve()

    task2 = FluentTask('fluent')
    task2.input_file = scm_solve_file
    task2.log_file = 'log_fluent.log'
    task2.additional_link_files = ['mesh.cdb']
    task2.results_files_names = ["log_fluent.log", "results.cas.h5", "results.dat.h5"]
    task2.solve()

    task3 = CFDPostTask('cfdpost')
    task3.input_file = cse_fluentpost_file
    task3.results_files_names = ["export.csv"]
    task3.solve()

    with open("export.csv", "r") as file:
        actual_result = len(file.readlines())
    assert actual_result == expected_result


@pytest.mark.positive
@pytest.mark.solve
def test_cfdpost__str__(tmpdir, cse_fluentpost_file, capsys):
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