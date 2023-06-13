import unittest
from caetask.caetask import FluentTask
import os


class TestFluentTask(unittest.TestCase):
    def setUp(self):
        os.chdir(os.environ.get('USERPROFILE'))
        if os.path.isfile("text_file_from_fluent.dat"):
            os.remove("text_file_from_fluent.dat")
        if os.path.isfile("test.scm"):
            os.remove("test.scm")
        if os.path.isfile("test.log"):
            os.remove("test.log")

    def test_fluent_task_start(self):
        with open("test.scm", "w") as file:
            file.write("(define out (open-output-file \"text_file_from_fluent.dat\"))\n")
            file.write("(display \"test text from fluent\" out)\n")
            file.write("(newline out)\n")
            file.write("(close-output-port out)\n")
            file.write("(ti-menu-load-string \"exit y\")\n")

        task1 = FluentTask('test')
        task1.input_file = 'test.scm'
        task1.solve()

        with open("text_file_from_fluent.dat", "r") as file:
            line_from_test_file = file.readline()
        self.assertEqual(line_from_test_file, "test text from fluent\n")

    def tearDown(self) -> None:
        os.chdir(os.environ.get('USERPROFILE'))
        if os.path.isfile("text_file_from_fluent.dat"):
            os.remove("text_file_from_fluent.dat")
        if os.path.isfile("test.scm"):
            os.remove("test.scm")
        if os.path.isfile("test.log"):
            os.remove("test.log")


if __name__ == '__main__':
    unittest.main()
