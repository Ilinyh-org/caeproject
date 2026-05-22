import pytest
from pathlib import Path
from caecase import CAECase


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


def test_case_path(tmp_path):
    case = CAECase.create_new(base_path=tmp_path)

    assert case.path == tmp_path / case.name
    assert case.path.exists()


