"""Unit tests for CAECase initialization, config persistence and get_csv_results CSV parsing."""
import json
import re
from pathlib import Path

import pytest

from caecase import CAECase
from caecase.caecase import CaseStatus, get_csv_results


@pytest.fixture
def temp_case_obj_path():
    """Provide and clean up a config file path in the current directory."""
    path = Path("test_caecase_obj.json")
    yield path
    if path.exists():
        path.unlink()


@pytest.fixture
def case_obj(tmp_path):
    """Create a fresh CAECase in a temporary directory."""
    return CAECase.create_new(base_path=tmp_path)


def test_case_initialization(tmp_path):
    """Verify create_new creates the case directory under the base path."""
    case = CAECase.create_new(base_path=tmp_path)
    expected_case_path = tmp_path / case.name

    assert expected_case_path.exists()


def test_case_initialization_wrong_path_type(tmpdir):
    """Verify create_new rejects a non-Path base path with TypeError."""
    with pytest.raises(TypeError):
        CAECase.create_new(base_path=tmpdir)


def test_case_initialization_custom_name(tmp_path):
    """Verify create_new honours a custom case name."""
    input_name = "myname"
    CAECase.create_new(base_path=tmp_path, name=input_name)
    expected_case_path = tmp_path / input_name

    assert expected_case_path.exists()


def test_case_sections(case_obj):
    """Verify a new case exposes parameters, tasks and status sections."""
    assert hasattr(case_obj, "parameters")
    assert hasattr(case_obj, "tasks")
    assert hasattr(case_obj, "status")


def test_case_path(tmp_path):
    """Verify the case path points to an existing named directory under the base path."""
    case = CAECase.create_new(base_path=tmp_path)

    assert case.path == tmp_path / case.name
    assert case.path.exists()


@pytest.fixture(scope="session")
def apdl_file(tmp_path_factory):
    """Write an APDL journal writing parameter text into a dat file; return its path."""
    fn = tmp_path_factory.mktemp("data") / "test.inp"
    with open(fn, "w", encoding="utf-8") as file:
        file.write("/batch\n")
        file.write("*dim,text,string,32,1\n")
        file.write("text(1)=\'test text from ansys\'\n")
        file.write("*cfopen,text_file_from_ansys,dat\n")
        file.write("*vwrite,H1,NES_H1\n")
        file.write("%G %I\n")
        file.write("*cfclos\n")
    return fn


def test_case_add_files_to_case(tmp_path, apdl_file):
    """Verify add_files_to_case copies the given file into the case directory."""
    case = CAECase.create_new(tmp_path)

    case.add_files_to_case([
        apdl_file,
    ])

    file_path = case.path / apdl_file.name
    assert file_path.exists(), f"File {file_path} does not exist"


def test_case_safe_config_files(tmp_path, apdl_file):
    """Verify save_config records added files in the config JSON."""
    expected_config = {
        "parameters": {},
        "files": ["test.inp"],
        "tasks": [],
        "status": 'NEW'
    }
    case = CAECase.create_new(tmp_path)
    case.add_files_to_case([
        apdl_file,
    ])

    case.save_config()

    with open(case.path / CAECase.CONFIG_DEFAULT_NAME, "r", encoding="utf-8") as f:
        actual_config = json.load(f)
    assert actual_config == expected_config


def test_case_load_config_files(tmp_path):
    """Verify load_config restores the file list, case name and base path."""
    case_name = "case_dir"
    data = {
        "parameters": {},
        "files": [
            "results.csv",
            "plots/figure.png"
        ],
        "tasks": [],
        "status": 'NEW'
    }
    expected_files = [
        Path("results.csv"),
        Path("plots/figure.png")
    ]
    expected_name = case_name
    expected_base_path = tmp_path
    case_dir_path = tmp_path / case_name
    case_dir_path.mkdir()
    with open(case_dir_path / "case_config.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    case = CAECase.load_config(case_dir_path)

    assert case.files == expected_files
    assert case.name == expected_name
    assert case.base_path == expected_base_path


def test_case_safe_config_status(tmp_path):
    """Verify save_config persists the case status."""
    expected_status = 'DONE'

    case = CAECase.create_new(tmp_path)
    case.status = CaseStatus.DONE

    case.save_config()

    with open(case.path / CAECase.CONFIG_DEFAULT_NAME, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == expected_status


def test_case_load_config_status(tmp_path):
    """Verify load_config restores the status, name and base path."""
    case_name = "case_dir"
    data = {
        "parameters": {},
        "files": [],
        "tasks": [],
        "status": "DONE"
    }
    expected_status = CaseStatus("DONE")
    expected_name = case_name
    expected_base_path = tmp_path
    case_dir_path = tmp_path / case_name
    case_dir_path.mkdir()
    with open(case_dir_path / "case_config.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    case = CAECase.load_config(case_dir_path)

    assert case.status == expected_status
    assert case.name == expected_name
    assert case.base_path == expected_base_path


def test_get_csv_results_plain_numbers_no_header(tmp_path):
    """Verify parsing a headerless single-column CSV of plain numbers."""
    f = tmp_path / "plain.csv"
    f.write_text(
        "2.22e+01\n"
        "2.22e+01\n"
        "0.00e+00\n"
        "0.00e+00\n"
        "0.00e+00\n"
        "0.00e+00\n"
    )
    expected_shape = (6, 1)
    expected_values = [22.2, 22.2, 0.0, 0.0, 0.0, 0.0]

    df = get_csv_results(f)

    assert df.shape == expected_shape
    assert df.iloc[:, 0].tolist() == expected_values


def test_get_csv_results_cfx_name_data_block(tmp_path):
    """Verify parsing a CFX [Name]/[Data] block CSV using the data header as column name."""
    f = tmp_path / "cfx_block.csv"
    f.write_text(
        "\n"
        "[Name]\n"
        "inlet\n"
        "\n"
        "[Data]\n"
        "Velocity u [ m s^-1 ]\n"
        "2.22e+01\n"
        "2.22e+01\n"
        "0.00e+00\n"
        "0.00e+00\n"
        "0.00e+00\n"
        "0.00e+00\n"
    )
    expected_shape = (6, 1)
    expected_values = [22.2, 22.2, 0.0, 0.0, 0.0, 0.0]
    expected_header = "Velocity u [ m s^-1 ]"

    df = get_csv_results(f)

    assert df.shape == expected_shape
    assert df.columns[0] == expected_header
    assert df.iloc[:, 0].tolist() == expected_values


def test_get_csv_results_header_then_values(tmp_path):
    """Verify parsing a CSV with a header line followed by numeric values."""
    f = tmp_path / "header.csv"
    f.write_text(
        "Velocity u\n"
        "2.22e+01\n"
        "2.22e+01\n"
        "0.00e+00\n"
        "0.00e+00\n"
        "0.00e+00\n"
        "0.00e+00\n"
    )
    expected_shape = (6, 1)
    expected_values = [22.2, 22.2, 0.0, 0.0, 0.0, 0.0]
    expected_header = "Velocity u"

    df = get_csv_results(f)

    assert df.shape == expected_shape
    assert df.columns[0] == expected_header
    assert df.iloc[:, 0].tolist() == expected_values


def test_get_csv_results_cfd_post_full_export(tmp_path):
    """Verify parsing a full CFD-Post export with comment preamble and [Name]/[Data] blocks."""
    f = tmp_path / "cfdpost.csv"
    f.write_text(
        "##\n"
        "## CFD-Post Generic Export\n"
        "##\n"
        "## CFX-21.2\n"
        "##\n"
        "## Generated on:  2026/09/21 14:37:56\n"
        "##\n"
        "## Generated from case(s): Case results.cas\n"
        "##\n"
        "\n"
        "[Name]\n"
        "inlet\n"
        "\n"
        "[Data]\n"
        "Velocity u [ m s^-1 ]\n"
        "2.22e+01\n"
        "2.22e+01\n"
        "0.00e+00\n"
        "0.00e+00\n"
        "0.00e+00\n"
        "0.00e+00\n"
    )
    expected_shape = (6, 1)
    expected_values = [22.2, 22.2, 0.0, 0.0, 0.0, 0.0]
    expected_header = "Velocity u [ m s^-1 ]"

    df = get_csv_results(f)

    assert df.shape == expected_shape
    assert df.columns[0] == expected_header
    assert df.iloc[:, 0].tolist() == expected_values


def test_get_csv_results_multi_column_csv(tmp_path):
    """Verify parsing a multi-column CSV with a header row."""
    f = tmp_path / "multi.csv"
    f.write_text(
        "U,V,W\n"
        "2.22e+01,0.00e+00,1.00e+00\n"
        "2.22e+01,0.00e+00,1.00e+00\n"
    )
    expected_shape = (2, 3)
    expected_values_u = [22.2, 22.2]
    expected_values_v = [0.0, 0.0]
    expected_values_w = [1.0, 1.0]
    expected_headers = ["U", "V", "W"]

    df = get_csv_results(f)

    assert list(df.columns) == expected_headers
    assert df.shape == expected_shape
    assert df["U"].tolist() == expected_values_u
    assert df["V"].tolist() == expected_values_v
    assert df["W"].tolist() == expected_values_w