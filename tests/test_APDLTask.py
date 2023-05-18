
import pytest
from CAETask import APDLTask
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed

lock = Lock()
# completed = 0
# total_tasks = 0


class TestAPDLTask:
    global lock, completed, total_tasks

    def setup_method(self):
        pass

    @pytest.mark.positive
    @pytest.mark.solve
    def test_apdl_solve(self, capsys):
        expected_result = "test text from ansys\n"
        with open("test.inp", "w") as file:
            file.write("/batch\n")
            file.write("*dim,text,string,32,1\n")
            file.write("text(1)=\'test text from ansys\'\n")
            file.write("*cfopen,text_file_from_ansys,dat\n")
            file.write("*vwrite,text(1)\n")
            file.write("%C\n")
            file.write("*cfclos\n")

        task = APDLTask('test')
        task.input_file = 'test.inp'
        task.results_files_names = ["text_file_from_ansys.dat"]
        task.solve()

        with open("text_file_from_ansys.dat", "r") as file:
            line_from_test_file = file.readline()
        assert line_from_test_file == expected_result

    @pytest.mark.positive
    @pytest.mark.solve
    @pytest.mark.input_parameters
    @pytest.mark.parametrize("input_data,expected_result",
                             [(1, 3.14),
                              (10, 31.4)])
    def test_apdl_calc_geom_vol(self, input_data, expected_result, capsys):
        pass

    @pytest.mark.positive
    @pytest.mark.solve
    @pytest.mark.input_parameters
    def test_apdl_multitask_prod(self, capsys):
        tasks = []  # список параллельных решаемых задач
        input_data = (('1', 1), ('2', 2))
        expected_results = (3, 6)

        def create_task(index):
            with open("test.inp", "w") as file:
                file.write("/batch\n")
                file.write("*cfopen,task" + input_data[index][0] + "_text_file,dat\n")
                file.write("*vwrite," + str(input_data[index][1]) + "*3\n")
                file.write("%I\n")
                file.write("*cfclos\n")
            task = APDLTask('test')
            task.input_file = 'test.inp'
            task.results_files_names = ["task" + input_data[index][0] + "_text_file.dat"]
            with lock:
                tasks.append(task)

        futures = []
        # with ThreadPoolExecutor(max_workers=10) as executor:
        with ProcessPoolExecutor(max_workers=10) as executor:
            for index in range(len(input_data)):
                futures.append(executor.submit(create_task(index)))

        total_tasks = len(tasks)
        completed = 0
        total_tasks = 0
        def completed_callback(future):
            global completed, total_tasks, lock
            with lock:
                completed += 1
                print("завершена задача в " + future.result().results_dir_path +
                      " осталось " + str(total_tasks - completed) + " задач")        #
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(task.solve) for task in tasks]
            for future in as_completed(futures):
                future.add_done_callback(completed_callback)

        for input, expected_result in zip(input_data, expected_results):
            with open("task" + input[0] + "_text_file.dat", "r") as file:
                actual_result = int(file.readline())
            assert actual_result == expected_result

    @pytest.mark.negative
    @pytest.mark.solve
    @pytest.mark.error_file
    def test_apdl_error(self, capsys):
        pass