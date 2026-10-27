"""Integration tests for CAECase parameters (set, grouped, item access),
serialization and config persistence."""
import json
import re
from pathlib import Path

import pytest

from caecase import CAECase
from caecase.caecase import CaseStatus
from core.parameter import Parameter


@pytest.fixture
def case_obj(tmp_path):
    """Create a fresh CAECase in a temporary directory."""
    return CAECase.create_new(base_path=tmp_path)


def test_case_set_parameter(case_obj):
    """Verify setting a top-level case parameter stores the given value."""
    input_value = 0
    expected_value = input_value

    case_obj.parameters.h1 = input_value

    actual_value = case_obj.parameters.h1.value
    assert actual_value == expected_value


def test_case_set_group_parameter(case_obj):
    """Verify setting a nested (grouped) parameter stores the given value."""
    input_value = 0.01
    expected_value = input_value

    case_obj.parameters.geometry.h1 = input_value

    actual_value = case_obj.parameters.geometry.h1.value
    assert actual_value == expected_value


def test_case_set_parameter_via_item(case_obj):
    """Verify setting a parameter via item access updates the same attribute."""
    input_value = True
    expected_value = input_value

    case_obj.parameters["cleanup"]["enabled"] = input_value

    actual_value = case_obj.parameters.cleanup.enabled.value
    assert actual_value == expected_value


def test_case_to_dict(case_obj):
    """Verify to_dict serializes parameters with units, files, tasks and status."""
    input_gravity = 9.8066
    input_units = "m/s²"
    input_files = ["input.txt", "output.txt"]
    case_obj.parameters.physics.gravity = Parameter(input_gravity, units=input_units)
    case_obj.files = input_files
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
        "status": "NEW"
    }

    actual_dict = case_obj.to_dict()

    assert actual_dict == expected_dict


def test_case_from_dict(tmp_path):
    """Verify from_dict restores parameters, status and files."""
    input_data = {
        "parameters": {
            "temperature": {
                "value": 500,
            }
        },
        "status": "RUNNING",
        "files": [
            "results.csv"
        ],
    }
    expected_parameter_temperature = 500
    expected_status = CaseStatus("RUNNING")
    expected_files = [Path("results.csv")]

    case = CAECase.from_dict(input_data, base_path=tmp_path)

    assert case.parameters.temperature == expected_parameter_temperature
    assert case.status == expected_status
    assert case.files == expected_files


def test_case_serialization_roundtrip(tmp_path):
    """Verify to_dict/from_dict roundtrip preserves parameters, status and files."""
    case = CAECase.create_new(tmp_path)
    case.parameters.alpha = 500
    case.status = CaseStatus("DONE")
    case.files = [Path("results.csv")]

    data = case.to_dict()

    restored = CAECase.from_dict(data, base_path=tmp_path)

    assert restored.parameters == case.parameters
    assert restored.status == case.status
    assert restored.files == case.files


def test_save_config(tmp_path):
    """Verify save_config writes the expected JSON config file."""
    expected_config = {
        "parameters": {
            "temperature": {'value': 300}
        },
        "status": "DONE",
        "files": [
            "results.csv"
        ],
        "tasks": []
    }
    case = CAECase.create_new(base_path=tmp_path)
    case.parameters.temperature = 300
    case.status = CaseStatus("DONE")
    case.files = ["results.csv"]

    case.save_config()

    config_path = case.path / CAECase.CONFIG_DEFAULT_NAME
    assert config_path.exists()
    with open(config_path, "r", encoding="utf-8") as f:
        actual_config = json.load(f)
    assert actual_config == expected_config


def test_load_config(tmp_path):
    """Verify load_config reads a config file into parameters, status and files."""
    expected_parameter_pressure = 42
    expected_status = CaseStatus("RUNNING")
    expected_files = [Path("output.dat")]
    config_data = {
        "parameters": {
            "pressure": {'value': 42}
        },
        "status": "RUNNING",
        "files": [
            "output.dat"
        ],
    }
    config_path = tmp_path / CAECase.CONFIG_DEFAULT_NAME
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f)

    case = CAECase.load_config(tmp_path)

    assert case.parameters.pressure == expected_parameter_pressure
    assert case.status == expected_status
    assert case.files == expected_files
