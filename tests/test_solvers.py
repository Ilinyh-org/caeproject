import os
import pytest
from caetask import run_processes, run_threads
from caetask import APDLTask
from threading import Lock

lock = Lock()


def create_task_chdir(index):  # задаётся пользователем
    import datetime
    import time
    import random
    # print('----'+os.path.abspath(os.curdir))
    print('CREATE_TASK_CHDIR')
    # global input_data

    resdir = None
    while True:
        try:
            resdir = datetime.datetime.now().isoformat().replace(':', '').replace('-', '_').replace('.', '_')
            # os.mkdir(wd_path + "\\" + resdir)
            os.mkdir("./" + resdir)
            break
        except FileExistsError:
            time.sleep(random.uniform(0.001, 0.01))
            continue
    try:
        # os.chdir(wd_path + "\\" + resdir)
        os.chdir(".\\" + resdir)
    except ValueError:
        raise
    # task_num = input_data[index][0]
    # num_par = input_data[index][1]

    # tempdir = "temp" + task_num
    # os.mkdir(tempdir)

    # with open(os.path.join(tempdir, "test.parm"), "w") as file:
    #     file.write("num=" + str(num_par))
    #
    # task = APDLTask('test')
    # task.input_file = 'test.inp'
    # task.parameters_file = os.path.join(tempdir, "test.parm")
    # task.results_files_names = ["task" + str(num_par) + "_text_file.dat"]
    return os.path.basename(os.path.abspath(os.curdir + "/../"))


@pytest.mark.positive
@pytest.mark.solve
@pytest.mark.input_parameters
def test_multitask_chdir(tmpdir, capsys):
    global input_data

    # expected_results = (3, 6, 9, 12, 15)
    expected_path = os.path.basename(os.path.abspath(tmpdir))
    os.chdir(tmpdir)

    # with open("test.inp", "w") as file:
    #     file.write("/batch\n")
    #     file.write("parres,change,test,parm\n")
    #     file.write("*cfopen,task%num%_text_file,dat\n")
    #     file.write("*vwrite,num*3\n")
    #     file.write("%I\n")
    #     file.write("*cfclos\n")
    # run_processes
    # run_threads
    parent_paths = run_processes(create_task_chdir, [1, 2, 3, 4, 5], max_workers=5)  # список параллельных решаемых задач

    for parent_path in parent_paths:
        assert parent_path == expected_path

    # run_threads(solve_task, tasks, max_workers=2)
    #
    # for input_sample, expected_result in zip(input_data, expected_results):
    #     with open("task" + input_sample[0] + "_text_file.dat", "r") as file:
    #         actual_result = int(file.readline())
    #     assert actual_result == expected_result