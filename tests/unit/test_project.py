from caeproject import CAEProject
import pandas as pd
from unittest.mock import MagicMock


def test_project_initialization(tmp_path):
    CAEProject.create_new(base_path=tmp_path)
    expected_project_dir = tmp_path / "project"

    assert expected_project_dir.exists()


def test_project_initialization_custom_name(tmp_path):
    CAEProject.create_new(base_path=tmp_path, name="myproject")
    expected_project_dir = tmp_path / "myproject"

    assert expected_project_dir.exists()


def test_project_get_results():
    expected_result = pd.DataFrame({
        "H1": [0.01, 0.02],
        "NES_H1": [2, 2],
    })
    case1 = MagicMock()
    case2 = MagicMock()
    case1.get_results.return_value = pd.DataFrame({
        "H1": [0.01],
        "NES_H1": [2],
    })
    case2.get_results.return_value = pd.DataFrame({
        "H1": [0.02],
        "NES_H1": [2],
    })
    project = MagicMock(spec=CAEProject)
    project.cases = {
        "case1": case1,
        "case2": case2,
    }

    actual_results = CAEProject.get_results(project)

    pd.testing.assert_frame_equal(actual_results, expected_result)
    case1.get_results.assert_called_once_with()
    case2.get_results.assert_called_once_with()

