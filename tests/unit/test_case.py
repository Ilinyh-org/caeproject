import json

import pytest
from pathlib import Path
from caecase import CAECase


@pytest.fixture
def temp_case_obj_path():
    path = Path("test_caecase_obj.json")
    yield path
    if path.exists():
        path.unlink()


@pytest.fixture
def case_obj(tmp_path):
    return CAECase.create_new(base_path=tmp_path)


def test_case_initialization(tmp_path):
    case = CAECase.create_new(base_path=tmp_path)
    expected_case_path = tmp_path / case.name

    assert expected_case_path.exists()


def test_case_initialization_wrong_path_type(tmpdir):
    with pytest.raises(TypeError):
        CAECase.create_new(base_path=tmpdir)


def test_case_initialization_custom_name(tmp_path):
    input_name = "myname"
    CAECase.create_new(base_path=tmp_path, name=input_name)
    expected_case_path = tmp_path / input_name

    assert expected_case_path.exists()


def test_case_sections(case_obj):
    assert hasattr(case_obj, "parameters")
    assert hasattr(case_obj, "tasks")
    assert hasattr(case_obj, "status")


def test_case_path(tmp_path):
    case = CAECase.create_new(base_path=tmp_path)

    assert case.path == tmp_path / case.name
    assert case.path.exists()


@pytest.fixture(scope="session")
def apdl_file(tmp_path_factory):
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


def test_case_add_files_to_case(tmp_path, apdl_file):
    case = CAECase.create_new(tmp_path)

    case.add_files_to_case([
        apdl_file,
    ])

    file_path = case.path / apdl_file.name
    assert file_path.exists(), f"File {file_path} does not exist"


def test_case_safe_config_files(tmp_path, apdl_file):
    expected_config = {
        "parameters": {},
        "files": ["test.inp"],
        "tasks": [],
        "status": {}
    }
    case = CAECase.create_new(tmp_path)
    case.add_files_to_case([
        apdl_file,
    ])

    case.save_config()

    with open(case.path / CAECase.CONFIG_DEFAULT_NAME, "r") as f:
        actual_config = json.load(f)
    assert actual_config == expected_config

def test_case_load_config_files(tmp_path, apdl_file):
    case_name = "case_dir"
    data = {
        "parameters": {},
        "files": [
            "results.csv",
            "plots/figure.png"
        ],
        "tasks": [],
        "status": {}
    }
    expected_files = [
        Path("results.csv"),
        Path("plots/figure.png")
    ]
    expected_name = case_name
    expected_base_path = tmp_path
    case_dir_path = tmp_path / case_name
    case_dir_path.mkdir()
    with open(case_dir_path / "case_config.json", "w") as f:
        json.dump(data, f, indent=2)

    case = CAECase.load_config(case_dir_path)

    assert case.files == expected_files
    assert case.name == expected_name
    assert case.base_path == expected_base_path


def test_case_safe_config_status(tmp_path):
    expected_status = {"state": "DONE"}

    case = CAECase.create_new(tmp_path)
    case.status = {"state": "DONE"}

    case.save_config()

    with open(case.path / CAECase.CONFIG_DEFAULT_NAME, "r") as f:
        data = json.load(f)
    assert data["status"] == expected_status


def test_case_load_config_status(tmp_path, apdl_file):
    case_name = "case_dir"
    data = {
        "parameters": {},
        "files": [],
        "tasks": [],
        "status": {"state": "DONE"}
    }
    expected_status = {"state": "DONE"}
    expected_name = case_name
    expected_base_path = tmp_path
    case_dir_path = tmp_path / case_name
    case_dir_path.mkdir()
    with open(case_dir_path / "case_config.json", "w") as f:
        json.dump(data, f, indent=2)

    case = CAECase.load_config(case_dir_path)

    assert case.status == expected_status
    assert case.name == expected_name
    assert case.base_path == expected_base_path

