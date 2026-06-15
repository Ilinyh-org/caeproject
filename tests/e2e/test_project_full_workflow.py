import pytest
from caetask import APDLTask, run_threads

from caecase import CAECase
from caeproject import CAEProject

import pandas as pd

from core.series_merger import series_merger


@pytest.fixture(scope="session")
def apdl_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "square_compression.inp"
    with open(fn, "w") as file:
        file.write("/batch\n")
        file.write("*dim,text,string,32,1\n")
        file.write("text(1)=\'test text from ansys\'\n")
        file.write("*cfopen,results,dat\n")
        file.write("*vwrite,H1,NES_H1\n")
        file.write("%G %I\n")
        file.write("*cfclos\n")
    return fn


def test_project_apdl_create_solve_get_results(tmp_path, apdl_file):
    # создание проекта
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

    def create_task(df):
        case = CAECase.create_new(tmp_project_path)
        case.parameters.geometry.H1 = df["H1"]
        case.parameters.geometry.H1.units = 'cm'
        case.parameters.geometry.B1 = df["B1"]
        case.parameters.geometry.B1.units = 'cm'
        case.parameters.mesh.NES_H1 = df["NES_H1"]
        case.parameters.mesh.NES_B1 = df["NES_B1"]

        case.add_files_to_case([
            apdl_file,
         # "macroslibrary.mac",
        ])
        case.parameters_save(format_type='APDL', new_system="SI") #TODO прописать имя

        task = APDLTask.create_new('square_compression')
        task.input_file = case.path / 'square_compression.inp'
        task.parameters_file = case.path / 'case_data.parm' # 'square_compression.parm'
        task.results_directory_path = case.path
        task.temporary_directory_path = tmp_wd_path
        task.log_file = 'log_square_compression.log'
        task.cores = 2
        task.results_files_names = [
            "log_square_compression.log",
            "square_compression0.err",
            "square_compression1.err",
            "RESULTS.dat",
        #     "RESULT_MODEL_INFO.CSV"
        ]

        # запуск решения проекта
        # project.solve()
        case.add_task(task)
        case.save_config()

        return task

    def solving(tasks):
        from collections.abc import Iterable  # TODO костыль
        if not isinstance(tasks, Iterable):
            tasks = [tasks]
        for task in tasks:
            task.solve()

    ## TODO запихнуть эти команды в проект?
    tasks = run_threads(create_task, df.to_dict(orient="records"), max_workers=1)
    run_threads(solving, tasks, max_workers=2)
    #
    # #подтянуть результаты
    project.discover_cases()


    for case in project.cases:
        print("1: ", case)

    #должен ли подтяигвать проект? да должен
    #результаты формируются автоматически на основе данных кейсов
    #нужен цикл по кейсам с обходмо резульатов
    #можно ли взять результаты не из кейсов? нет они не сохраняется
    #типы результатов в блокноете

    #обработать результаты
    #нарисовать график(?)
    #

    # в отдельном тест прочекать конфигурации

    pass
    # initial_case_parameter = 100
    # project = CAEProject.from_existing_dir(tmp_path)
    # existing_case = CAECase.create_new(base_path=tmp_path)
    # existing_case.parameters.a = initial_case_parameter
    # project.cases.append(existing_case)
    # parameters_set = {0, 1, 2}
    # expected_parameters = {0, 1, 2, 100}
    #
    # for a in parameters_set:
    #     case = CAECase.create_new(base_path=tmp_path)
    #     case.parameters.a = a
    #     case.save_config(case.path)
    #
    # project.discover_cases()
    #
    # actual_parameters = {case.parameters.a.value for case in project.cases}
    #
    # assert len(actual_parameters) == len(expected_parameters)
    # assert actual_parameters == expected_parameters
    # assert initial_case_parameter in actual_parameters


def test_project_create_solve_get_results3(tmp_path):
    ##создать проект
    # добавить исходные данные
    # запустить кейсы
    # решить

    # создать новый проект на основе директории
    # подтянуть результаты
    # обработать результаты
    # нарисовать график(?)
    #
    pass


def test_project_create_solve_get_results2(tmp_path):
    ##создать проект
    # добавить исходные данные
    # запустить кейсы
    # решить

    #создать новый проект на основе директории
    # подтянуть результаты
    # обработать результаты
    # нарисовать график(?)
    #
    pass


## в этом или отдельном файле запустить параллельное решение задач