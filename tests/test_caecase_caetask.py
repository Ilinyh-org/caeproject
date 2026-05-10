
import pytest
from pathlib import Path
from caecase import CAECase
from caetask import APDLTask
from core import Parameter
import os, json


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
    caecase1 = CAECase(tmpdir)
    caecase1.parameters.geometry.H1 = 5
    caecase1.parameters.geometry.H1.units = 'cm'
    caecase1.parameters.mesh.NES_H1 = 11

    caecase1.parameters_save()

    actual_file_content = json.load(caecase1.path / "case_data.json")
    assert actual_file_content == expected_file_content


def test_caecase_parameters_partial_include_option(tmpdir):
    expected_file_content = {
        'geometry': {
        "H1": {
            "value": 5,
            "units": "cm",
        }}
    }
    caecase1 = CAECase(tmpdir)
    caecase1.parameters.geometry.H1 = 5
    caecase1.parameters.geometry.H1.units = 'cm'
    caecase1.parameters.mesh.NES_H1 = 11

    caecase1.parameters_save(include=['geometry'])

    actual_file_content = json.load(caecase1.path / "case_data.json")
    assert actual_file_content == expected_file_content


def test_caecase_parameters_partial_exclude_option(tmpdir):
    expected_file_content = {
        'geometry': {
        "H1": {
            "value": 5,
            "units": "cm",
        }}
    }
    caecase1 = CAECase(tmpdir)
    caecase1.parameters.geometry.H1 = 5
    caecase1.parameters.geometry.H1.units = 'cm'
    caecase1.parameters.mesh.NES_H1 = 11

    caecase1.parameters_save(exclude=['mesh'])

    actual_file_content = json.load(caecase1.path / "case_data.json")
    assert actual_file_content == expected_file_content


def test_caecase_parameters_conversion_apdl(tmpdir):
    caecase1 = CAECase(tmpdir)
    expected_file_content = '!geometry\nH1=0.05 ![m]\n!mesh\nNES_H1=11\n'
    caecase1.parameters.geometry.H1 = 5
    caecase1.parameters.geometry.H1.units = 'cm'
    caecase1.parameters.mesh.NES_H1 = 11

    caecase1.parameters_save(format_type='APDL', new_system="SI")

    with open(caecase1.path / "case_data.parm") as file:
        actual_file_content = file.read()

    assert actual_file_content == expected_file_content


def test_caecase_parameters_conversion_apdl_partial(tmpdir):
    pass


@pytest.fixture(scope="session")
def apdl_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "test.inp"
    with open(fn, "w") as file:
        file.write("/batch\n")
        file.write("parres,,test,parm\n")
        file.write("*cfopen,text_file_from_ansys,dat\n")
        file.write("*vwrite,A1+B1\n")
        file.write("%G\n")
        file.write("*cfclos\n")
    return fn


@pytest.mark.positive
@pytest.mark.solve
def test_apdl_solve(tmpdir, apdl_file):
    expected_file_content = '5\n'
    caecase1 = CAECase(tmpdir)
    caecase1.add_files_to_case(apdl_file)
    caecase1.parameters.A1 = 2
    caecase1.parameters.B1 = 3
    caecase1.parameters_save(filename='test', format_type='APDL')

    task = APDLTask('test')
    task.results_directory_path = caecase1.path
    task.input_file = caecase1.path / "test.inp"
    task.parameters_file = caecase1.path / "test.parm"
    task.results_files_names = ["text_file_from_ansys.dat"]

    caecase1.tasks.append(task)

    caecase1.solve()

    with open(caecase1.path / "text_file_from_ansys.dat", "r") as file:
        actual_file_content = file.read()
    assert actual_file_content == expected_file_content
