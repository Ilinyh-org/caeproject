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

    res_dir = None
    while True:
        try:
            res_dir = datetime.datetime.now().isoformat().replace(':', '').replace('-', '_').replace('.', '_')
            os.mkdir("./" + res_dir)
            break
        except FileExistsError:
            time.sleep(random.uniform(0.001, 0.01))
            continue
    try:
        os.chdir(".\\" + res_dir)
    except ValueError:
        raise

    return os.path.basename(os.path.abspath(os.curdir + "/../"))


@pytest.mark.positive
@pytest.mark.solve
@pytest.mark.input_parameters
@pytest.mark.parametrize("input_data",
                         [([1, 2, 3, 4, 5], 1),
                          ([1, 2, 3, 4, 5, 6, 7], 4),
                          ([1, 2, 3, 4, 5, 6, 7, 8, 9], 9),
                          ([1, 2, 3, 4], 8)])
def test_multitask_chdir(tmpdir, input_data, capsys):
    tasks_input_data = input_data[0]
    max_workers = input_data[1]
    expected_path = os.path.basename(os.path.abspath(tmpdir))

    os.chdir(tmpdir)
    parent_paths = run_processes(create_task_chdir, tasks_input_data, max_workers=max_workers)

    for parent_path in parent_paths:
        assert parent_path == expected_path
