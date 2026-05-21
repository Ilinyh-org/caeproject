
import json
import pytest
from pathlib import Path
from caecase import CAECase
from core import Parameter


@pytest.fixture
def temp_caecase_obj_path():
    path = Path("test_caecase_obj.json")
    yield path
    if path.exists():
        path.unlink()


@pytest.fixture
def caecase_obj(tmp_path):
    return CAECase.create_new(base_path=tmp_path)

# @pytest.fixture
# def caecase_obj(tmp_path):
#     caecase = CAECase(tmp_path / "caecase_obj.json")
#     caecase.files = ["input.txt", "output.txt"]
#     return caecase

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


def test_caecase_sections(caecase_obj):
    assert hasattr(caecase_obj, "parameters")
    assert hasattr(caecase_obj, "tasks")
    assert hasattr(caecase_obj, "status")


def test_caecase_set_parameter(caecase_obj):
    input_value = 0
    expected_value = input_value

    caecase_obj.parameters.h1 = input_value

    actual_value = caecase_obj.parameters.h1.value
    assert actual_value == expected_value


def test_caecase_set_group_parameter(caecase_obj):
    input_value = 0.01
    expected_value = input_value

    caecase_obj.parameters.geometry.h1 = input_value

    actual_value = caecase_obj.parameters.geometry.h1.value
    assert actual_value == expected_value


def test_caecase_set_parameter_via_item(caecase_obj):
    input_value = True
    expected_value = input_value

    caecase_obj.parameters["cleanup"]["enabled"] = input_value

    actual_value = caecase_obj.parameters.cleanup.enabled.value
    assert actual_value == expected_value


def test_caecase_to_dict(caecase_obj):
    input_gravity = 9.8066
    input_units = "m/s²"
    input_files = ["input.txt", "output.txt"]
    caecase_obj.parameters.physics.gravity = Parameter(input_gravity, units=input_units)
    caecase_obj.files = input_files
    expected_dict = {
        "parameters": {
            "physics": {
                "gravity": {
                    "value": input_gravity,
                    "units": input_units
                }
            }
        },
        "files": input_files,
        "tasks": [],
        "status": {}
    }

    actual_dict = caecase_obj.to_dict()

    assert actual_dict == expected_dict


def test_case_from_dict(tmp_path):
    input_data = {
        "parameters": {
            "temperature": {
                "value": 500,
            }
        },
        "status": {
            "state": "RUNNING"
        },
        "files": [
            "results.csv"
        ],
    }
    expected_parameter_temperature = 500
    expected_status = {"state": "RUNNING"}
    expected_files = ["results.csv"]

    case = CAECase.from_dict(input_data, base_path=tmp_path)

    assert case.parameters.temperature == expected_parameter_temperature
    assert case.status == expected_status
    assert case.files == expected_files


def test_case_serialization_roundtrip(tmp_path):
    case = CAECase(tmp_path)
    case.parameters.alpha = 500
    case.status = {"state": "DONE"}
    case.files = ["results.csv"]

    data = case.to_dict()

    restored = CAECase.from_dict(data, base_path=tmp_path)

    assert restored.parameters == case.parameters
    assert restored.status == case.status
    assert restored.files == case.files


def test_case_path(tmp_path):
    case = CAECase.create_new(base_path=tmp_path)

    assert case.path == tmp_path / case.name
    assert case.path.exists()

def test_save_config(tmp_path):
    expected_config = {
        "parameters": {
            "temperature": {'value': 300}
        },
        "status": {
            "state": "DONE"
        },
        "files": [
            "results.csv"
        ],
        "tasks": []
    }
    case = CAECase.create_new(base_path=tmp_path)
    case.parameters.temperature = 300
    case.status = {"state": "DONE"}
    case.files = ["results.csv"]

    case.save_config()

    config_path = case.path / CAECase.CONFIG_DEFAULT_NAME
    assert config_path.exists()
    with open(config_path, "r") as f:
        actual_config = json.load(f)
    assert actual_config == expected_config


def test_load_config(tmp_path):
    expected_parameter_pressure = 42
    expected_status = {"state": "RUNNING"}
    expected_files = ["output.dat"]
    config_data = {
        "parameters": {
            "pressure": {'value': 42}
        },
        "status": {
            "state": "RUNNING"
        },
        "files": [
            "output.dat"
        ],
    }
    config_path = tmp_path / CAECase.CONFIG_DEFAULT_NAME
    with open(config_path, "w") as f:
        json.dump(config_data, f)

    case = CAECase.load_config(tmp_path, base_path=tmp_path)

    assert case.parameters.pressure == expected_parameter_pressure
    assert case.status == expected_status
    assert case.files == expected_files