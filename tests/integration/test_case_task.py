import shutil
from pathlib import Path

import pytest
from caecase import CAECase
from caetask import APDLTask, FluentTask
import json
import os


def test_case_check_directory(tmp_path):
    case = CAECase.create_new(base_path=tmp_path)

    assert case.path.exists()


def test_create_case_apdltask(tmp_path):
    case = CAECase.create_new(tmp_path)

    task = case.create_task(APDLTask, "square_compression")
    task.input_file = "square_compression.inp"
    task.parameters_file = "square_compression.parm"
    task.log_file_name = "log_square_compression.log"
    task.results_files_names = [
        "square_compression0.err",
        "square_compression1.err",
        "RESULTS.csv",
    ]

    assert task.name == "square_compression"
    assert task.base_path == case.path
    assert task.input_file.name == "square_compression.inp"
    assert task.parameters_file.name == "square_compression.parm"
    assert task.log_file_name == "log_square_compression.log"
    assert task.results_files_names == [
        "square_compression0.err",
        "square_compression1.err",
        "RESULTS.csv",
    ]

    assert task.case is case
    assert task in case.tasks


def test_create_case_with_attributes_apdltask(tmp_path):
    case = CAECase.create_new(tmp_path)

    task = case.create_task(
        APDLTask,
        "square_compression",
        input_file="square_compression.inp",
        parameters_file="square_compression.parm",
        results_files_names=["RESULTS.csv"],
    )

    assert task.name == "square_compression"
    assert task.base_path == case.path
    assert task.input_file.name == "square_compression.inp"
    assert task.parameters_file.name == "square_compression.parm"
    assert task.results_files_names == ["RESULTS.csv"]

    assert task.case is case
    assert task in case.tasks


def test_create_case_fluenttask(tmp_path):
    case = CAECase.create_new(tmp_path)

    task = case.create_task(APDLTask, "pump")
    task.input_file = "pump.scm"
    task.parameters_file = "pump_parm.scm"
    task.log_file_name = "log_pump.log"
    task.results_files_names = [
        "RESULTS.csv",
    ]

    assert task.name == "pump"
    assert task.base_path == case.path
    assert task.input_file.name == "pump.scm"
    assert task.parameters_file.name == "pump_parm.scm"
    assert task.log_file_name == "log_pump.log"
    assert task.results_files_names == [
        "RESULTS.csv",
    ]

    assert task.case is case
    assert task in case.tasks


def test_create_case_with_attributes_fluenttask(tmp_path):
    case = CAECase.create_new(tmp_path)

    task = case.create_task(
        FluentTask,
        "pump",
        input_file="pump.scm",
        parameters_file="pump_parm.scm",
        results_files_names=["RESULTS.csv"],
    )

    assert task.name == "pump"
    assert task.base_path == case.path
    assert task.input_file.name == "pump.scm"
    assert task.parameters_file.name == "pump_parm.scm"
    assert task.results_files_names == ["RESULTS.csv"]

    assert task.case is case
    assert task in case.tasks


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


@pytest.fixture(scope="session")
def text_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "text.txt"
    with open(fn, "w") as file:
        file.write("simple text\n")
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

    task = APDLTask.create_new('test')
    task.results_directory = case.path
    task.input_file = case.path / apdl_file.name
    task.parameters_file = case.path / "test.parm"
    task.results_files_names = ["text_file_from_ansys.dat"]

    case.tasks.append(task)

    case.solve()

    with open(case.path / "text_file_from_ansys.dat", "r") as file:
        actual_file_content = file.read()
    assert actual_file_content == expected_file_content


@pytest.fixture(scope="session")
def apdl_file_empty(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "test.inp"
    with open(fn, "w") as file:
        file.write("/batch\n")
    return fn


@pytest.mark.positive
@pytest.mark.solve
@pytest.mark.log
def test_apdl_solve_log_file(tmp_path, apdl_file_empty):
    expected_log_file_name = 'test.log'
    expected_log_text_parts = [
        "Ansys Mechanical",
        "W E L C O M E   T O   T H E   A N S Y S (R)  P R O G R A M",
        "ANSYS COMMAND LINE ARGUMENTS",
        "A N S Y S   S T A T I S T I C S",
        "ANSYS RUN COMPLETED"]

    case = CAECase.create_new(tmp_path)
    case.add_files_to_case(apdl_file_empty)

    task = APDLTask.create_new('test')
    task.results_directory = case.path
    task.input_file = case.path / apdl_file_empty.name

    case.tasks.append(task)

    case.solve()

    assert Path(case.path / expected_log_file_name).exists()
    with open(case.path / expected_log_file_name, "r") as file:
        log_text = file.read()
        for expected_log_text_part in expected_log_text_parts:
            assert expected_log_text_part in log_text


def test_case_safe_config_task(tmp_path, apdl_file):
    expected_config = {
        "parameters": {'A1': {'value': 2}, 'B1': {'value': 3}},
        "files": ["test.inp"],
        'tasks': [{
            'type': 'apdl',
            'additional_link_files': [],
            'additional_text_files': [],
            'additional_text_files_codes': [],
            'application_version': '212',
            'copy_link_files': False,
            'cores': '2',
            'database_size': '1024',
            'geometry_file': '',
            'memory_size': '2048',
            'name': 'test',
            'new_parameter_name': None,
            'new_parameter_value': None,
            'parameters_file': 'test.parm',
            'results_directory': '.',
            'results_file_name': None,
            'results_files_names': ['text_file_from_ansys.dat'],
            'input_file': apdl_file.name,
            'log_file_name': 'test.log',
            'status': None}],
        "status": "NEW"
    }

    case = CAECase.create_new(tmp_path)
    case.add_files_to_case(apdl_file)
    case.parameters.A1 = 2
    case.parameters.B1 = 3
    case.parameters_save(filename='test.parm', format_type='APDL')

    task = case.create_task(APDLTask, 'test')
    task.input_file = apdl_file
    task.parameters_file = "test.parm"
    task.results_files_names = ["text_file_from_ansys.dat"]
    task.solve()
    case.save_config()

    with open(case.path / CAECase.CONFIG_DEFAULT_NAME, "r") as f:
        actual_config = json.load(f)
    assert actual_config == expected_config


def test_case_safe_config_task_link_files(tmp_path, apdl_file, text_file):
    expected_config = {
        "parameters": {'A1': {'value': 2}, 'B1': {'value': 3}},
        "files": ["test.inp"],
        'tasks': [{
            'type': 'apdl',
            'additional_link_files': ['text.txt'],
            'additional_text_files': [],
            'additional_text_files_codes': [],
            'application_version': '212',
            'copy_link_files': False,
            'cores': '2',
            'database_size': '1024',
            'geometry_file': '',
            'memory_size': '2048',
            'name': 'test',
            'new_parameter_name': None,
            'new_parameter_value': None,
            'parameters_file': 'test.parm',
            'results_directory': '.',
            'results_file_name': None,
            'results_files_names': ['text_file_from_ansys.dat'],
            'input_file': apdl_file.name,
            'log_file_name': 'test.log',
            'status': None}],
        "status": "NEW"
    }

    case = CAECase.create_new(tmp_path)
    case.add_files_to_case(apdl_file)
    case.add_files_to_case(text_file)
    case.parameters.A1 = 2
    case.parameters.B1 = 3
    case.parameters_save(filename='test.parm', format_type='APDL')

    task = case.create_task(APDLTask, 'test')
    task.input_file = apdl_file
    task.additional_link_files = ['text.txt']
    task.parameters_file = "test.parm"
    task.results_files_names = ["text_file_from_ansys.dat"]
    # task.solve()
    case.save_config()

    with open(case.path / CAECase.CONFIG_DEFAULT_NAME, "r") as f:
        actual_config = json.load(f)
    assert actual_config == expected_config


@pytest.fixture(scope="session")
def config_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "case.json"
    config = {
        "parameters": {'A1': {'value': 2}, 'B1': {'value': 3}},
        "files": ["test.inp"],
        'tasks': [{
            'type':'apdl',
            'name': 'test',
            'additional_link_files': [],
            'additional_text_files': [],
            'additional_text_files_codes': [],
            'application_version': '212',
            'copy_link_files': False,
            'cores': '2',
            'database_size': '1024',
            'geometry_file': None,
            'memory_size': '2048',
            'new_parameter_name': None,
            'new_parameter_value': None,
            'parameters_file': 'test.parm',
            'results_directory': '.',
            'results_file_name': '',
            'results_files_names': ['text_file_from_ansys.dat'],
            'input_file': 'test.inp',
            'log_file_name': 'test.log',
            'status': None}],
        "status": "NEW"
    }

    with open(fn, "w") as file:
        json.dump(config, file)
    return fn


def test_case_task_from_dict(tmp_path, config_file):
    case_dir = tmp_path / "case_dir"
    case_dir.mkdir()
    os.chdir(case_dir)

    with open(config_file) as file:
        input_config = json.load(file)
    expected_task_config = input_config['tasks'][0]
    expected_parameters = input_config['parameters']
    expected_files = input_config['files']

    case = CAECase.from_dict(input_config, base_path=case_dir.parent, name=case_dir.name)

    actual_task_config = case.tasks[0].to_dict()
    actual_parameters = case.parameters.to_dict()
    actual_files = [str(file) for file in case.files]
    assert actual_task_config == expected_task_config
    assert actual_parameters == expected_parameters
    assert actual_files == expected_files


def test_case_task_load_config(tmp_path, config_file):
    case_dir = tmp_path / "case_dir"
    case_dir.mkdir()
    os.chdir(case_dir)
    config_file = shutil.copy2(config_file, case_dir)

    with open(config_file) as file:
        input_config = json.load(file)
    expected_task_config = input_config['tasks'][0]
    expected_parameters = input_config['parameters']
    expected_files = input_config['files']
    expected_base_path = tmp_path
    expected_case_name = case_dir.name

    case = CAECase.load_config(config_file)

    actual_base_path = case.base_path
    actual_case_name = case.name
    actual_task_config = case.tasks[0].to_dict()
    actual_parameters = case.parameters.to_dict()
    actual_files = [str(file) for file in case.files]
    assert actual_base_path == expected_base_path
    assert actual_case_name == expected_case_name
    assert actual_task_config == expected_task_config
    assert actual_parameters == expected_parameters
    assert actual_files == expected_files


