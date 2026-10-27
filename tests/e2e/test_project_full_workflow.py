
import pandas as pd
import plotly.express as px
import pytest

from caecase import CAECase
from caecase.utils import is_case_dir_name
from caetask import APDLTask, run_threads
from caeproject import CAEProject

from core.series_merger import series_merger
from workflows.apdl import APDLWorkflow
from workflows.apdl_fluent_cfdpost import APDLFluentCFDPostWorkflow


@pytest.fixture(scope="session")
def apdl_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "square_compression.inp"
    with open(fn, "w", encoding="utf-8") as file:
        file.write("finish\n")
        file.write("/clear\n")
        file.write("/prep7\n")
        file.write("h1=0.1\n")
        file.write("u=0.01\n")
        file.write("parres,new,square_compression,parm\n")
        file.write("et,1,183\n")
        file.write("mp,ex,1,2e11\n")
        file.write("mp,nuxy,1,0.3\n")
        file.write("blc4,,,h1/2,h1/2\n")
        file.write("esize,,1\n")
        file.write("amesh,all\n")
        file.write("lsel,s,loc,y\n")
        file.write("nsll,s,1\n")
        file.write("d,all,uy\n")
        file.write("lsel,s,loc,x\n")
        file.write("nsll,s,1\n")
        file.write("d,all,ux\n")
        file.write("lsel,s,loc,y,h1/2\n")
        file.write("nsll,s,1\n")
        file.write("d,all,uy,-u\n")
        file.write("/solu\n")
        file.write("allsel\n")
        file.write("solve\n")
        file.write("/post1\n")
        file.write("set,last\n")
        file.write("etab,stab,s,y\n")
        file.write("*get,s,elem,1,etab,stab\n")
        file.write("*cfopen,results,csv\n")
        file.write("*vwrite\n")
        file.write("S\n")
        file.write("*vwrite,S\n")
        file.write("%G\n")
        file.write("*cfclos\n")
    return fn


def test_project_apdl_create_solve_get_results(tmp_path, apdl_file):
    expected_results_dataframe = pd.DataFrame(
        {
            "H1": pd.Series([0.1, 0.1, 0.2, 0.2], dtype="float64"),
            "U": pd.Series([0.01, 0.02, 0.01, 0.02], dtype="float64"),
            "S": pd.Series([-4e10, -8e10, -2e10, -4e10], dtype="float64"),
        }
    )
    expected_results_dataframe_length = 4
    expected_results_cases_number = 4

    # Project creation
    tmp_project_path = tmp_path / "project"
    tmp_project_path.mkdir()
    tmp_wd_path = tmp_path / "wd"
    tmp_wd_path.mkdir()

    project = CAEProject.from_existing_dir(tmp_project_path)

    ds_H1 = pd.Series([0.1, 0.2], dtype="float64", name="H1")
    ds_U = pd.Series([0.01, 0.02], dtype="float64", name="U")

    df = series_merger(
        ds_H1, ds_U,
    )

    def create_case(row):
        case = CAECase.create_new(tmp_project_path)

        case.parameters.geometry.H1 = row["H1"]
        case.parameters.geometry.H1.units = "m"

        case.parameters.loads.U = row["U"]
        case.parameters.loads.U.units = "m"

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

    assert len(df_res) == expected_results_dataframe_length
    assert df_res["ID"].nunique() == expected_results_cases_number
    assert all(is_case_dir_name(case_id) for case_id in df_res["ID"])  # check the cases names
    pd.testing.assert_frame_equal(
        df_res[["H1", "U", "S"]].reset_index(drop=True),
        expected_results_dataframe,
    )


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
            "H1": pd.Series([0.1, 0.1, 0.2, 0.2], dtype="float64"),
            "U": pd.Series([0.01, 0.02, 0.01, 0.02], dtype="float64"),
            "S": pd.Series([-4e10, -8e10, -2e10, -4e10], dtype="float64"),
        }
    )
    expected_results_dataframe_length = 4

    tmp_project_path = tmp_path / "project"
    tmp_project_path.mkdir()

    project = CAEProject.from_existing_dir(tmp_project_path)

    ds_H1 = pd.Series([0.1, 0.2], dtype="float64", name="H1")
    ds_U = pd.Series([0.01, 0.02], dtype="float64", name="U")

    df = series_merger(
        ds_H1, ds_U,
    )

    def configure_case(case, row):
        case.parameters.geometry.H1 = row["H1"]
        case.parameters.geometry.H1.units = "m"

        case.parameters.loads.U = row["U"]
        case.parameters.loads.U.units = "m"

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

    assert len(df_res) == expected_results_dataframe_length
    assert all(is_case_dir_name(case_id) for case_id in df_res["ID"])  # check the cases names
    pd.testing.assert_series_equal(
        df_res[["H1", "U"]].nunique(),
        expected_results_dataframe[["H1", "U"]].nunique()
    )
    pd.testing.assert_frame_equal(
        df_res[["H1", "U", "S"]].dropna().reset_index(drop=True),
        expected_results_dataframe,
        check_dtype=True,
        rtol=1e-5,
        atol=1e-4
    )


@pytest.fixture(scope="session")
def inp_mesh_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "poiseuille_flow.inp"
    with open(fn, "w", encoding="utf-8") as file:
        file.write("finish\n")
        file.write("/clear\n")
        file.write("/prep7\n")
        file.write("r1=0.2\n")
        file.write("l1=2.0\n")
        file.write("nes_r1=4\n")
        file.write("space_r1=5\n")
        file.write("parres,change,poiseuille_flow,parm\n")
        file.write("/prep7\n")
        file.write("et,1,200,6\n")
        file.write("blc4,,,l1,r1\n")
        file.write("lsel,s,loc,x,l1\n")
        file.write("lreverse,all\n")
        file.write("lsel,s,length,,r1\n")
        file.write("lesize,all,,,nes_r1,space_r1\n")
        file.write("lsel,s,length,,l1\n")
        file.write("lesize,all,r1/nes_r1\n")
        file.write("amesh,all\n")
        file.write("lsel,s,loc,x\n")
        file.write("nsll,s,1\n")
        file.write("cm,inlet,node\n")
        file.write("lsel,s,loc,x,l1\n")
        file.write("nsll,s,1\n")
        file.write("cm,outlet,node\n")
        file.write("lsel,s,loc,y\n")
        file.write("nsll,s,1\n")
        file.write("cm,axis,node\n")
        file.write("lsel,s,loc,y,r1\n")
        file.write("nsll,s,1\n")
        file.write("cm,wall,node\n")
        file.write("allsel\n")
        file.write("cm,fluid,elem\n")
        file.write("cdopt,iges\n")
        file.write("cdwrite,all,mesh,cdb\n")
    return fn


@pytest.fixture(scope="session")
def scm_solve_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "poiseuille_flow.scm"
    with open(fn, "w", encoding="utf-8") as file:
        file.write("(ti-menu-load-string \"/file/import/mechanical-apdl/input mesh.cdb\")\n")
        file.write("(ti-menu-load-string \"/define/models axisymmetric? y\")\n")
        file.write("(ti-menu-load-string \"/define/models/viscous/laminar? y\")\n")
        file.write("(ti-menu-load-string \"/define/materials/copy fluid water-liquid\")\n")
        file.write("(ti-menu-load-string \"/define/boundary-conditions/fluid fluid y water-liquid n n n n y n\")\n")
        file.write("(ti-menu-load-string "
                   "\"/define/boundary-conditions/zone-type inlet mass-flow-inlet\")\n")
        file.write("(ti-menu-load-string "
                   "\"/define/boundary-conditions mass-flow-inlet "
                   "inlet y y n 1.0 n 0 y n 1 n\")\n")  # mass flow inlet
        file.write("(ti-menu-load-string \"/solve/monitors/residual/convergence-criteria 1e-9 1e-9 1e-9\")\n")
        file.write("(ti-menu-load-string \"/solve/iterate 500\")\n")
        file.write("(ti-menu-load-string \"/file/write-case results.cas.h5\")\n")
        file.write("(ti-menu-load-string \"/file/write-data results.dat.h5\")\n")
        file.write("(ti-menu-load-string \"exit y\")\n")
    return fn


@pytest.fixture(scope="session")
def cse_cfdpost_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "poiseuille_flow.cse"
    with open(fn, "w", encoding="utf-8") as file:
        file.write("!use lib '.';\n")
        file.write("!use JsonConfig;\n")
        file.write("!my $p = load_params('poiseuille_flow.json');\n")
        file.write("!my $l1 = $p->{l1};\n")
        file.write("!my $r1 = $p->{r1};\n")
        file.write("!my $point1x = $l1*0.9;\n")
        file.write(">load filename=results.cas.h5, force_reload=true\n")
        file.write("LINE: line1\n")
        file.write("  Domain List = /DOMAIN GROUP:All Domains\n")
        file.write("  Line Samples = 5\n")
        file.write("  Line Type = Sample\n")
        file.write("  Line Width = 2\n")
        file.write("  Option = Two Points\n")
        file.write("  Point 1 = $point1x [m], 0 [m], 0 [m]\n")
        file.write("  Point 2 = $point1x [m], $r1 [m], 0 [m]\n")
        file.write("  Range = Global\n")
        file.write("  Visibility = Off\n")
        file.write("END\n")
        file.write("POINT: point1\n")
        file.write("  Option = XYZ\n")
        file.write("  Point = $point1x [m], 0 [m], 0 [m]\n")
        file.write("END\n")
        file.write("LIBRARY:\n")
        file.write("  CEL:\n")
        file.write("    EXPRESSIONS:\n")
        file.write("      pressure = probe(Pressure)@point1\n")
        file.write("      Q = pressure * pi * ($r1 [m])^4 / (8 * ($l1 - $point1x) [m] * 0.001003[Pa s])\n")
        file.write("    END\n")
        file.write("  END\n")
        file.write("END\n")
        file.write("EXPORT:\n")
        file.write("  CSV Type = CSV\n")
        file.write("  Export File = RESULTS_VELOCITY.csv\n")
        file.write("  Export Geometry = Off\n")
        file.write("  Location List = /LINE: line1\n")
        file.write("  Overwrite = On\n")
        file.write("  Precision = 2\n")
        file.write('  Separator = ", "\n')
        file.write("  Variable List = Y, Velocity\n")
        file.write("END\n")
        file.write(">export\n")
        file.write("TABLE: table1\n")
        file.write("  Table Exists = True\n")
        file.write("  Table Export Separator = Comma\n")
        file.write("  TABLE CELLS:\n")
        file.write('    A1 = "Q", False, False, False, Left, True, 0, Font Name, 1|1, %10.1e, True, ffffff, 000000, True\n')
        file.write('    A2 = "=Q", False, False, False, Left, True, 0, Font Name, 1|1, %14.4e, False, ffffff, 000000, True\n')
        file.write('    B1 = "pressure", False, False, False, Left, True, 0, Font Name, 1|1, %10.1e, True, ffffff, 000000, True\n')
        file.write('    B2 = "=pressure", False, False, False, Left, True, 0, Font Name, 1|1, %14.4e, False, ffffff, 000000, True\n')
        file.write("  END\n")
        file.write("END\n")
        file.write(">table save=RESULTS.csv, name=table1\n")
    return fn


def test_project_apdl_fluent_cfdpost_workflow(
        tmp_path,
        inp_mesh_file,
        scm_solve_file,
        cse_cfdpost_file,
):
    expected_results_dataframe = pd.DataFrame(
        {
            "R1": pd.Series([0.1, 0.2], dtype="float64"),
            "L1": pd.Series([5, 5], dtype="float64"),
            "NES_R1": pd.Series([5, 5], dtype="int64"),
            "Q": pd.Series([0.001987, 0.001992], dtype="float64"),
        }
    )
    expected_results_dataframe_length = 12

    tmp_project_path = tmp_path / "project"
    tmp_project_path.mkdir()

    project = CAEProject.from_existing_dir(tmp_project_path)

    ds_R1 = pd.Series([0.1, 0.2], dtype="float64", name="R1")  # 0.05,
    ds_L1 = pd.Series([5], dtype="float64", name="L1")
    ds_NES_R1 = pd.Series([5], dtype="int64", name="NES_R1")

    df = series_merger(
        ds_R1,
        ds_L1,
        ds_NES_R1,
    )

    def configure_case(case, row):
        case.parameters.geometry.R1 = row["R1"]
        case.parameters.geometry.R1.units = "m"

        case.parameters.geometry.L1 = row["L1"]
        case.parameters.geometry.L1.units = "m"

        case.parameters.mesh.NES_R1 = row["NES_R1"]

    workflow = APDLFluentCFDPostWorkflow(
        project=project,
        apdl_file=inp_mesh_file,
        fluent_file=scm_solve_file,
        cfdpost_file=cse_cfdpost_file,
        task_name="poiseuille_flow",
        configure_case=configure_case,
    )

    workflow.create_cases(
        df.to_dict(orient="records"),
        max_workers=1,
    )

    project.solve(max_workers=2)

    project.discover_cases()

    df_res = project.get_results()

    assert len(df_res) == expected_results_dataframe_length
    assert all(is_case_dir_name(case_id) for case_id in df_res["ID"])  # check the cases names
    pd.testing.assert_series_equal(
        df_res[["R1", "L1", "NES_R1"]].nunique(),
        expected_results_dataframe[["R1", "L1", "NES_R1"]].nunique()
    )
    pd.testing.assert_frame_equal(
        df_res[["R1", "L1", "NES_R1", 'Q']].dropna().reset_index(drop=True),
        expected_results_dataframe,
        check_dtype=True,
        rtol=1e-5,
        atol=1e-4
    )
