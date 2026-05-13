import json
from pathlib import Path

from caecase import CAECase
from caeproject import CAEProject


def test_project_discovers_cases(tmp_path):
    cases_number = 3
    created_cases = []

    for i in range(cases_number):
        case = CAECase(base_path=tmp_path)
        case.parameters.index = i

        case_dir = case.path
        case.save_config(case_dir)
        created_cases.append(case)

    project = CAEProject(base_path=tmp_path)

    project.discover_cases() ## cсоздаёт папки при создании объектов, т.е. нужно создание на оснвое существующего оъекта, что нужно указать в load_config

    assert len(project.cases) == cases_number

    # indices = sorted(
    #     case.parameters["index"]
    #     for case in project.cases
    # )
    #
    # assert indices == [0, 1, 2]
    #
    # for case in project.cases:
    #     assert case.status["state"] == "DONE"
    #
    #     config_path = (
    #         case.base_path /
    #         case.CONFIG_DEFAULT_NAME
    #     )
    #
    #     assert config_path.exists()