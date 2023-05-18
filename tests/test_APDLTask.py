import unittest
import pytest
from CAETask import APDLTask
import os
from threading import Lock

lock = Lock()
completed = 0
total_tasks = 0

class TestAPDLTask:
    global lock, completed, total_tasks

    def setup_method(self):
        pass

    @pytest.mark.datatypes
    def test_integer(self, capsys):
        input_data = '1456'
        expected_result = '(INTEGER,\'1456\',2,0)\n'

        klex.run(input_data)
        actual_result = capsys.readouterr().out
        assert actual_result == expected_result


        XMLConv.toapdl('trubki.xml', ['materials', 'geometry', 'mesh', 'bc', 'solver'], 'trubki.parm', 'w')
        task = APDLTask('trubki')
        task.input_file = wd_path + "\\" + '__mem_glad_test.DAT'
        task.parameters_file = wd_path + "\\" + resdir + "\\" + 'trubki.parm'
        task.log_file = wd_path + "\\" + resdir + "\\" + 'log_trubki.log'
        task.results_dir_path = wd_path + "\\" + resdir
        task.application_version = '212'
        task.cores = 4
        # task.additional_files = [wd_path + "\\" + "prop_visc_gyp.dat",
        #                          wd_path + "\\" + "atg.out",
        #                          wd_path + "\\" + "bet.out",
        #                          wd_path + "\\" + "c.out",
        #                          wd_path + "\\" + "e80.out",
        #                          wd_path + "\\" + "moon120.out",
        #                          wd_path + "\\" + "moon140.out",
        #                          wd_path + "\\" + "moon160.out"]
        # task.results_files_names = ["RESULT_PRES.CSV",
        #                             "MEM_G.db",
        #                             "MEM_G.rst",
        #                             "trubki0.err",
        #                             "trubki1.err"]
        with lock:
            tasks.append(task)
        return 0

        def completed_callback(future):
            global completed, total_tasks, lock
            with lock:
                completed += 1
                print("завершена задача в " + future.result().results_dir_path +
                      " осталось " + str(total_tasks - completed) + " задач")
        #
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(task.solve) for task in tasks]
            for future in as_completed(futures):
                future.add_done_callback(completed_callback)

        print("--- расчёты шли %s секунд ---" % (time.time() - start_time))

        return 0


# class TestAPDLTask(unittest.TestCase):
#     def setUp(self):
#         os.chdir(os.environ.get('USERPROFILE'))
#         if os.path.isfile("text_file_from_ansys.dat"):
#             os.remove("text_file_from_ansys.dat")
#         if os.path.isfile("test.inp"):
#             os.remove("test.inp")
#
#     def test_apdl_task_start(self):
#         with open("test.inp", "w") as file:
#             file.write("/batch\n")
#             file.write("*dim,text,string,32,1\n")
#             file.write("text(1)=\'test text from ansys\'\n")
#             file.write("*cfopen,text_file_from_ansys,dat\n")
#             file.write("*vwrite,text(1)\n")
#             file.write("%C\n")
#             file.write("*cfclos\n")
#
#         task1 = APDLTask('test')
#         task1.input_file = 'test.inp'
#         task1.solve()
#
#         with open("text_file_from_ansys.dat", "r") as file:
#             line_from_test_file = file.readline()
#         self.assertEqual(line_from_test_file, "test text from ansys\n")
#
#     def tearDown(self) -> None:
#         os.chdir(os.environ.get('USERPROFILE'))
#         if os.path.isfile("text_file_from_ansys.dat"):
#             os.remove("text_file_from_ansys.dat")
#         if os.path.isfile("test.inp"):
#             os.remove("test.inp")
#         if os.path.isfile("test.err"):
#             os.remove("test.err")
#         if os.path.isfile("test.log"):
#             os.remove("test.log")
#         if os.path.isfile("test.db"):
#             os.remove("test.db")
#
#
# if __name__ == '__main__':
#     unittest.main()
