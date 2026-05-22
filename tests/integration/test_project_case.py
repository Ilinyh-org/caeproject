import json

from caecase import CAECase
from caeproject import CAEProject


def test_project_discovers_cases(tmp_path):
    created_cases = []
    parameters_set = {0, 1, 2}
    for parameter_a in parameters_set:
        case = CAECase.create_new(tmp_path)
        case.parameters.a = parameter_a
        case.save_config()
        created_cases.append(case)

    project = CAEProject.from_existing_dir(tmp_path)

    project.discover_cases()

    received_parameters_set = {case.parameters.a.value for case in project.cases}
    assert len(project.cases) == len(parameters_set)
    assert received_parameters_set == parameters_set
    for case in project.cases:
        assert case.path.exists()


def test_project_discovers_cases_into_existing_project(tmp_path):
    initial_case_parameter = 100
    project = CAEProject.from_existing_dir(tmp_path)
    existing_case = CAECase.create_new(base_path=tmp_path)
    existing_case.parameters.a = initial_case_parameter
    project.cases.append(existing_case)
    parameters_set = {0, 1, 2}
    expected_parameters = {0, 1, 2, 100}

    for a in parameters_set:
        case = CAECase.create_new(base_path=tmp_path)
        case.parameters.a = a
        case.save_config(case.path)

    project.discover_cases()

    actual_parameters = {case.parameters.a.value for case in project.cases}

    assert len(actual_parameters) == len(expected_parameters)
    assert actual_parameters == expected_parameters
    assert initial_case_parameter in actual_parameters


def test_project_save_config(tmp_path):
    parameters_set = {0, 1, 2}

    project = CAEProject(base_path=tmp_path, name="test_project")
    for a in parameters_set:
        case = CAECase.create_new(base_path=tmp_path)
        case.parameters.a = a
        project.cases.append(case)

    project.save_config(tmp_path)

    config_path = tmp_path / project.CONFIG_DEFAULT_NAME

    assert config_path.exists()
    with open(config_path, "r") as f:
        data = json.load(f)
    assert data["name"] == "test_project"
    assert len(data["cases"]) == len(parameters_set)


def test_project_add_case(tmp_path):
    project = CAEProject(base_path=tmp_path)
    case = CAECase.create_new(tmp_path)#base_path=tmp_path)
    case.parameters.a = 42
    case.save_config()

    project.add_case(case)

    assert len(project.cases) == 1
    added_case = project.cases[0]
    assert added_case.parameters["a"].value == 42
    assert added_case.path.exists()

    config_path = added_case.path / added_case.CONFIG_DEFAULT_NAME
    assert config_path.exists()
