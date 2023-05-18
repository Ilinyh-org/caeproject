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

    @pytest.mark.positive
    @pytest.mark.solve
    def test_apdl_solve(self, capsys):
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
        assert line_from_test_file, "test text from ansys\n"

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
    def test_apdl_multitask(self, capsys):
        pass

    @pytest.mark.negative
    @pytest.mark.solve
    @pytest.mark.error_file
    def test_apdl_error(self, capsys):
        pass