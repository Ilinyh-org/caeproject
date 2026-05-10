
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
    return CAECase(tmp_path)


# @pytest.fixture
# def caecase_obj(tmp_path):
#     caecase = CAECase(tmp_path / "caecase_obj.json")
#     caecase.files = ["input.txt", "output.txt"]
#     return caecase


def test_caecase_sections(caecase_obj):
    assert hasattr(caecase_obj, "parameters")
    assert hasattr(caecase_obj, "_files")
    assert hasattr(caecase_obj, "tasks")
    assert hasattr(caecase_obj, "status")


def test_caecase_set_parameter(caecase_obj):
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
