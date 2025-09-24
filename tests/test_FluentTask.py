
import pytest
from caetask import FluentTask
import os


def setup_method():
    # os.chdir(os.environ.get('USERPROFILE'))
    # if os.path.isfile("text_file_from_fluent.dat"):
    #     os.remove("text_file_from_fluent.dat")
    # if os.path.isfile("test.scm"):
    #     os.remove("test.scm")
    # if os.path.isfile("test.log"):
    #     os.remove("test.log")
    pass

@pytest.mark.positive
@pytest.mark.solve
def test_fluent_task_start():
    expected_result = "test text from fluent\n"

    with open("test.scm", "w") as file:
        file.write("(define out (open-output-file \"text_file_from_fluent.dat\"))\n")
        file.write("(display \"test text from fluent\" out)\n")
        file.write("(newline out)\n")
        file.write("(close-output-port out)\n")
        file.write("(ti-menu-load-string \"exit y\")\n")

    task1 = FluentTask('test')
    task1.input_file = 'test.scm'
    task1.results_files_names = ["text_file_from_fluent.dat"]
    task1.solve()

    with open("text_file_from_fluent.dat", "r") as file:
        actual_result = file.readline()
        assert actual_result == expected_result




# def tearDown() -> None:
#     os.chdir(os.environ.get('USERPROFILE'))
#     if os.path.isfile("text_file_from_fluent.dat"):
#         os.remove("text_file_from_fluent.dat")
#     if os.path.isfile("test.scm"):
#         os.remove("test.scm")
#     if os.path.isfile("test.log"):
#         os.remove("test.log")


