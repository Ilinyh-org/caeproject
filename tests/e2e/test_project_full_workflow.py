
import pytest
from caecase import CAECase
from caecase.utils import is_case_dir_name
from caetask import APDLTask, run_threads
from caeproject import CAEProject

import pandas as pd
import plotly.express as px

from core.series_merger import series_merger
from workflows.apdl import APDLWorkflow


@pytest.fixture(scope="session")
def apdl_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "square_compression.inp"
    with open(fn, "w") as file:
        file.write("/batch\n")
        file.write("parres,new,square_compression,parm\n")
        file.write("*dim,text,string,32,1\n")
        file.write("text(1)=\'test text from ansys\'\n")
        file.write("*cfopen,results,csv\n")
        file.write("*vwrite\n")
        file.write("H1,NES_H1\n")
        file.write("*vwrite,H1,NES_H1\n")
        file.write("%G, %I\n")
        file.write("*cfclos\n")
    return fn


def test_project_apdl_create_solve_get_results(tmp_path, apdl_file):
    expected_results_dataframe = pd.DataFrame(
        {
            "H1": [0.01, 0.02],
            "NES_H1": [2, 2],
        }
    )

    # Project creation
    tmp_project_path = tmp_path / "project"
    tmp_project_path.mkdir()
    tmp_wd_path = tmp_path / "wd"
    tmp_wd_path.mkdir()

    project = CAEProject.from_existing_dir(tmp_project_path)

    ds_H1 = pd.Series([1, 2], dtype='float64', name="H1")  #[cm]
    ds_B1 = pd.Series([1], dtype='float64', name="B1")  #[cm]
    ds_L1 = pd.Series([10], dtype='float64', name="L1")  #[cm]
    ds_NES_H1 = pd.Series([2], dtype='int64', name="NES_H1")
    ds_NES_B1 = pd.Series([2], dtype='int64', name="NES_B1")
    ds_NES_L1 = pd.Series([20], dtype='int64', name="NES_L1")

    df = series_merger(ds_H1, ds_B1, ds_L1, ds_NES_H1, ds_NES_B1, ds_NES_L1)

    def create_case(row):
        case = CAECase.create_new(tmp_project_path)

        case.parameters.geometry.H1 = row["H1"]
        case.parameters.geometry.H1.units = 'cm'
        case.parameters.geometry.B1 = row["B1"]
        case.parameters.geometry.B1.units = 'cm'
        case.parameters.mesh.NES_H1 = row["NES_H1"]
        case.parameters.mesh.NES_B1 = row["NES_B1"]

        case.add_files_to_case([apdl_file])

        case.parameters_save(filename='square_compression.parm' , format_type='APDL', new_system="SI")

        task = case.create_task(APDLTask, 'square_compression')
        task.input_file = 'square_compression.inp'
        task.parameters_file = 'square_compression.parm'
        task.log_file_name = 'log_square_compression.log'
        task.results_files_names = [
            "square_compression0.err",
            "square_compression1.err",
            "RESULTS.csv",
            # "RESULT_MODEL_INFO.CSV"
        ]

        case.save_config()

        return case

    project.create_cases(
        df.to_dict(orient="records"),
        create_case,
        max_workers=1,
    )

    project.solve(max_workers=2)

    # Get results from file system
    project.discover_cases()

    df_res = project.get_results()

    # Plot results chart
    #fig = px.bar(df_res, x='ID', y='H1', title='Bar Plot Example')
    #fig.show()

    # Compare all deterministic columns
    pd.testing.assert_frame_equal(
        df_res[["H1", "NES_H1"]].reset_index(drop=True),
        expected_results_dataframe,
    )

    # Check the ID column
    assert len(df_res) == 2
    assert all(is_case_dir_name(case_id) for case_id in df_res["ID"])
    assert df_res["ID"].is_unique


def test_project_create_solve_get_results_short_task(tmp_path, apdl_file):
    expected_results_dataframe = pd.DataFrame(
        {
            "H1": [0.01, 0.02],
            "NES_H1": [2, 2],
        }
    )

    # Project creation
    tmp_project_path = tmp_path / "project"
    tmp_project_path.mkdir()
    tmp_wd_path = tmp_path / "wd"
    tmp_wd_path.mkdir()

    project = CAEProject.from_existing_dir(tmp_project_path)

    ds_H1 = pd.Series([1, 2], dtype='float64', name="H1")  # [cm]
    ds_B1 = pd.Series([1], dtype='float64', name="B1")  # [cm]
    ds_L1 = pd.Series([10], dtype='float64', name="L1")  # [cm]
    ds_NES_H1 = pd.Series([2], dtype='int64', name="NES_H1")
    ds_NES_B1 = pd.Series([2], dtype='int64', name="NES_B1")
    ds_NES_L1 = pd.Series([20], dtype='int64', name="NES_L1")

    df = series_merger(ds_H1, ds_B1, ds_L1, ds_NES_H1, ds_NES_B1, ds_NES_L1)

    def create_case(row):
        case = CAECase.create_new(tmp_project_path)

        case.parameters.geometry.H1 = row["H1"]
        case.parameters.geometry.H1.units = 'cm'
        case.parameters.geometry.B1 = row["B1"]
        case.parameters.geometry.B1.units = 'cm'
        case.parameters.mesh.NES_H1 = row["NES_H1"]
        case.parameters.mesh.NES_B1 = row["NES_B1"]

        case.add_files_to_case([apdl_file])

        case.parameters_save(filename='square_compression.parm', format_type='APDL', new_system="SI")

        task = case.create_task(
            APDLTask,
            "square_compression",
            input_file="square_compression.inp",
            parameters_file="square_compression.parm",
            log_file_name='log_square_compression.log',
            results_files_names=["RESULTS.csv"],
        )

        case.save_config()

        return case

    project.create_cases(
        df.to_dict(orient="records"),
        create_case,
        max_workers=1,
    )

    project.solve(max_workers=2)

    # Get results from file system
    project.discover_cases()

    df_res = project.get_results()

    # Plot results chart
    # fig = px.bar(df_res, x='ID', y='H1', title='Bar Plot Example')
    # fig.show()

    # Compare all deterministic columns
    pd.testing.assert_frame_equal(
        df_res[["H1", "NES_H1"]].reset_index(drop=True),
        expected_results_dataframe,
    )

    # Check the ID column
    assert len(df_res) == 2
    assert all(is_case_dir_name(case_id) for case_id in df_res["ID"])
    assert df_res["ID"].is_unique


def test_project_apdl_workflow(tmp_path, apdl_file):
    expected_results_dataframe = pd.DataFrame(
        {
            "H1": [0.01, 0.02],
            "NES_H1": [2, 2],
        }
    )

    tmp_project_path = tmp_path / "project"
    tmp_project_path.mkdir()

    project = CAEProject.from_existing_dir(tmp_project_path)

    ds_H1 = pd.Series([1, 2], dtype="float64", name="H1")
    ds_B1 = pd.Series([1], dtype="float64", name="B1")
    ds_L1 = pd.Series([10], dtype="float64", name="L1")
    ds_NES_H1 = pd.Series([2], dtype="int64", name="NES_H1")
    ds_NES_B1 = pd.Series([2], dtype="int64", name="NES_B1")
    ds_NES_L1 = pd.Series([20], dtype="int64", name="NES_L1")

    df = series_merger(
        ds_H1, ds_B1, ds_L1,
        ds_NES_H1, ds_NES_B1, ds_NES_L1,
    )

    def configure_case(case, row):
        case.parameters.geometry.H1 = row["H1"]
        case.parameters.geometry.H1.units = "cm"

        case.parameters.geometry.B1 = row["B1"]
        case.parameters.geometry.B1.units = "cm"

        case.parameters.mesh.NES_H1 = row["NES_H1"]
        case.parameters.mesh.NES_B1 = row["NES_B1"]

    workflow = APDLWorkflow(
        project=project,
        apdl_file=apdl_file,
        task_name="square_compression",
        configure_case=configure_case,
    )

    workflow.create_cases(
        df.to_dict(orient="records"),
        max_workers=1,
    )

    project.solve(max_workers=2)

    project.discover_cases()

    df_res = project.get_results()

    pd.testing.assert_frame_equal(
        df_res[["H1", "NES_H1"]].reset_index(drop=True),
        expected_results_dataframe,
    )

    assert len(df_res) == 2
    assert all(is_case_dir_name(case_id) for case_id in df_res["ID"])
    assert df_res["ID"].is_unique