
import pytest
from pathlib import Path
from caecase import CAECase, Parameter
from caetask import APDLTask
import os, json


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


def test_caecase_check_directory(tmpdir):
    caecase1 = CAECase(tmpdir)

    assert caecase1.path.exists()


@pytest.fixture(scope="session")
def apdl_file2(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "test.inp"
    with open(fn, "w") as file:
        file.write("/batch\n")
        file.write("*dim,text,string,32,1\n")
        file.write("text(1)=\'test text from ansys\'\n")
        file.write("*cfopen,text_file_from_ansys,dat\n")
        file.write("*vwrite,H1,NES_H1\n")
        file.write("%G %I\n")
        file.write("*cfclos\n")
    return fn


def test_caecase_add_files_to_case(tmpdir, apdl_file2):
    caecase1 = CAECase(tmpdir)

    caecase1.add_files_to_case([
        apdl_file2,
    ])

    file_path = caecase1.path / apdl_file2.name
    assert file_path.exists(), f"File {file_path} does not exist"


def test_caecase_parameters(tmpdir):
    caecase1 = CAECase(tmpdir)
    expected_file_content = {
        'geometry': {
        "H1": {
            "value": 5,
            "units": "cm",
        }},
        'mesh':{
        "NES_H1": {
            "value": 11,
        }}
    }
    caecase1.parameters.geometry.H1 = 5
    caecase1.parameters.geometry.H1.units = 'cm'
    caecase1.parameters.mesh.NES_H1 = 11

    caecase1.parameters_save()

    actual_file_content = json.load(caecase1.path / "case_data.json")
    assert actual_file_content == expected_file_content


def test_caecase_parameters_conversion_apdl(tmpdir):
    caecase1 = CAECase(tmpdir)
    expected_file_content = 'H1=5 ![cm]\nNES_H1=11\n'
    caecase1.parameters.geometry.H1 = 5
    caecase1.parameters.geometry.H1.units = 'cm'
    caecase1.parameters.mesh.NES_H1 = 11

    caecase1.parameters_save(format='apdl')

    actual_file_content = json.load(caecase1.path / "case_data.json")
    assert actual_file_content == expected_file_content


def test_caecase_parameters_conversion_apdl_partial(tmpdir):
    pass


    # xmlconv.toapdl(PATH, ['materials', 'geometry', 'mesh', 'bc', 'solver'], os.path.join(resdir, 'filter1d.parm'), 'w')
    # xmlconv.toscheme(PATH, ['materials', 'geometry', 'mesh', 'bc', 'solver'], os.path.join(resdir, 'filter1d_parm.scm'), 'w')
    # xmlconv.toperl(PATH, ['materials', 'geometry', 'mesh', 'bc', 'solver'], os.path.join(resdir, 'filter1d.pl'), 'w')

    # task = APDLTask('test')
    # task.input_file = apdl_file
    # task.results_files_names = ["text_file_from_ansys.dat"]
    # task.solve()
