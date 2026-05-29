
import pytest
from pathlib import Path
from caecase import CAECase
from caetask import APDLTask
from core.parameter import Parameter
import os, json


def test_case_check_directory(tmp_path):
    case = CAECase.create_new(base_path=tmp_path)

    assert case.path.exists()


def test_case_parameters(tmp_path):
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
    case = CAECase.create_new(tmp_path)
    case.parameters.geometry.H1 = 5
    case.parameters.geometry.H1.units = 'cm'
    case.parameters.mesh.NES_H1 = 11

    case.parameters_save()

    with open(case.path / "case_data.json", 'r') as f:
        actual_file_content = json.load(f)
    assert actual_file_content == expected_file_content


def test_case_parameters_partial_include_option(tmp_path):
    expected_file_content = {
        'geometry': {
        "H1": {
            "value": 5,
            "units": "cm",
        }}
    }
    case = CAECase.create_new(tmp_path)
    case.parameters.geometry.H1 = 5
    case.parameters.geometry.H1.units = 'cm'
    case.parameters.mesh.NES_H1 = 11

    case.parameters_save(include=['geometry'])

    with open(case.path / "case_data.json", 'r') as f:
        actual_file_content = json.load(f)
    assert actual_file_content == expected_file_content


def test_case_parameters_partial_exclude_option(tmp_path):
    expected_file_content = {
        'geometry': {
        "H1": {
            "value": 5,
            "units": "cm",
        }}
    }
    case = CAECase.create_new(tmp_path)
    case.parameters.geometry.H1 = 5
    case.parameters.geometry.H1.units = 'cm'
    case.parameters.mesh.NES_H1 = 11

    case.parameters_save(exclude=['mesh'])

    with open(case.path / "case_data.json", 'r') as f:
        actual_file_content = json.load(f)
    assert actual_file_content == expected_file_content


def test_case_parameters_conversion_apdl(tmp_path):
    case = CAECase.create_new(tmp_path)
    expected_file_content = '!geometry\nH1=0.05 ![m]\n!mesh\nNES_H1=11\n'
    case.parameters.geometry.H1 = 5
    case.parameters.geometry.H1.units = 'cm'
    case.parameters.mesh.NES_H1 = 11

    case.parameters_save(format_type='APDL', new_system="SI")

    with open(case.path / "case_data.parm") as file:
        actual_file_content = file.read()

    assert actual_file_content == expected_file_content


def test_case_parameters_conversion_apdl_partial(tmp_path):
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
def test_apdl_solve(tmp_path, apdl_file):
    expected_file_content = '5\n'
    case = CAECase.create_new(tmp_path)
    case.add_files_to_case(apdl_file)
    case.parameters.A1 = 2
    case.parameters.B1 = 3
    case.parameters_save(filename='test', format_type='APDL')

    task = APDLTask('test')
    task.results_directory_path = case.path
    task.input_file = case.path / "test.inp"
    task.parameters_file = case.path / "test.parm"
    task.results_files_names = ["text_file_from_ansys.dat"]

    case.tasks.append(task)

    case.solve()

    with open(case.path / "text_file_from_ansys.dat", "r") as file:
        actual_file_content = file.read()
    assert actual_file_content == expected_file_content
