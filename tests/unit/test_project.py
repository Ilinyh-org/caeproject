"""Unit tests for CAEProject: project creation and results aggregation."""
from unittest.mock import MagicMock

import pandas as pd

from caeproject import CAEProject


def test_project_initialization(tmp_path):
    """Verify CAEProject.create_new creates the project directory under the given base path."""
    CAEProject.create_new(base_path=tmp_path)
    expected_project_dir = tmp_path / "project"

    assert expected_project_dir.exists()


def test_project_initialization_custom_name(tmp_path):
    """Verify create_new honours a custom project name for the project directory."""
    CAEProject.create_new(base_path=tmp_path, name="myproject")
    expected_project_dir = tmp_path / "myproject"

    assert expected_project_dir.exists()


def test_project_get_results():
    """Verify get_results merges each case's parameters and results into one DataFrame."""
    expected_result = pd.DataFrame({
        "H1": [0.01, 0.02],
        "NES_H1": [2, 2],
        "U": [1E-3, 2E-3],
    })
    case1 = MagicMock()
    case2 = MagicMock()

    case1.parameters.to_dataframe.return_value = pd.DataFrame({
        "H1": [0.01],
        "NES_H1": [2],
    })
    case2.parameters.to_dataframe.return_value = pd.DataFrame({
        "H1": [0.02],
        "NES_H1": [2],
    })
    case1.get_results.return_value = pd.DataFrame({
        "U": [1E-3],
    })
    case2.get_results.return_value = pd.DataFrame({
        "U": [2E-3],
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

