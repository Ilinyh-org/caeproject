from caeproject import CAEProject


def test_project_initialization(tmp_path):
    CAEProject.create_new(base_path=tmp_path)
    expected_project_dir = tmp_path / "project"

    assert expected_project_dir.exists()


def test_project_initialization_custom_name(tmp_path):
    CAEProject.create_new(base_path=tmp_path, name="myproject")
    expected_project_dir = tmp_path / "myproject"

    assert expected_project_dir.exists()


