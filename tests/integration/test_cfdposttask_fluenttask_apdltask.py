"""Integration tests chaining APDLTask, FluentTask and CFDPostTask solves (requires solver backends)."""
import os
from pathlib import Path

import pytest

from caetask import APDLTask, FluentTask, CFDPostTask


@pytest.fixture(scope="session")
def cse_cfdpost_file(tmp_path_factory):
    """Write a CFD-Post session file exporting inlet velocity to CSV; return its path."""
    fn = tmp_path_factory.mktemp("data") / "test.cse"
    with open(fn, "w", encoding="utf-8") as file:
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
def test_cfdposttask_get_csv_results(tmpdir, inp_mesh_file, scm_solve_file, cse_cfdpost_file):
    """Verify the APDL→Fluent→CFD-Post pipeline exports a CSV with the expected number of lines."""
    tmpdir.chdir()
    expected_result = 6

    task1 = APDLTask.create_new('apdl')
    task1.input_file = inp_mesh_file
    task1.results_files_names = ["mesh.cdb"]
    task1.solve()

    task2 = FluentTask.create_new('fluent')
    task2.input_file = scm_solve_file
    task2.log_file_name = 'log_fluent.log'
    task2.additional_link_files = ['mesh.cdb']
    task2.results_files_names = ["results.cas.h5", "results.dat.h5"]
    task2.solve()

    task3 = CFDPostTask.create_new('cfdpost')
    task3.input_file = cse_cfdpost_file
    task3.results_files_names = ["export.csv"]
    task3.solve()

    with open("export.csv", "r", encoding="utf-8") as file:
        actual_result = len(file.readlines())
    assert actual_result == expected_result


@pytest.mark.positive
@pytest.mark.solve
def test_cfdposttask_not_in_current_directory(tmp_path: Path,
                                              inp_mesh_file, scm_solve_file, cse_cfdpost_file):
    """Verify chained tasks succeed with results and working directories outside the current directory."""
    tmpdir1 = tmp_path / "tmpdir1"
    tmpdir1.mkdir()
    tmpdir2 = tmp_path / "tmpdir2"
    tmpdir2.mkdir()
    tmpdir1.cwd()

    expected_result = 6

    task1 = APDLTask.create_new('apdl')
    task1.input_file = inp_mesh_file
    task1.results_directory = tmpdir2
    task1.results_files_names = ["mesh.cdb"]
    task1.solve()

    task2 = FluentTask.create_new('fluent')
    task2.input_file = scm_solve_file
    task2.log_file_name = 'log_fluent.log'
    task2.additional_link_files = [tmpdir2 / 'mesh.cdb']
    task2.results_directory = tmpdir2
    task2.results_files_names = ["log_fluent.log", "results.cas.h5", "results.dat.h5"]
    task2.solve()

    task3 = CFDPostTask.create_new('cfdpost')
    task3.input_file = cse_cfdpost_file
    task3.working_directory = os.path.abspath(tmpdir2)
    task3.results_files_names = ["export.csv"]
    task3.solve()

    with open(tmpdir2 / "export.csv", "r", encoding="utf-8") as file:
        actual_result = len(file.readlines())
    assert actual_result == expected_result


@pytest.fixture(scope="session")
def inp_mesh_file(tmp_path_factory):
    """Write an APDL script meshing a square with inlet/outlet/wall components; return its path."""
    fn = tmp_path_factory.mktemp("data") / "mesh.inp"
    with open(fn, "w", encoding="utf-8") as file:
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
    """Write a Fluent journal importing the mesh, solving one iteration and writing case/data; return its path."""
    fn = tmp_path_factory.mktemp("data") / "test.scm"
    with open(fn, "w", encoding="utf-8") as file:
        file.write("(ti-menu-load-string \"/file/import/mechanical-apdl/input mesh.cdb\")\n")
        file.write("(ti-menu-load-string \"/solve/iterate 1\")\n")
        file.write("(ti-menu-load-string \"/file/write-case results.cas.h5\")\n")
        file.write("(ti-menu-load-string \"/file/write-data results.dat.h5\")\n")
        file.write("(ti-menu-load-string \"exit y\")\n")
    return fn
