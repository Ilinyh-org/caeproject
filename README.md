# caeproject

A module for running CAE applications from python script.

A CAE project contains one or more CAE cases; each case runs CAE tasks
(e.g. ANSYS APDL) in its own folder. Tasks are a combination of a command
script, parameters and results file names.

## Installation

Requires Python >= 3.12. From source:

```
pip install git+https://github.com/Ilinyh-org/caeproject.git
```

Dependencies: `pint`, `pandas`.

## Versions

The package version is derived automatically from git tags with
[setuptools-scm](https://setuptools-scm.readthedocs.io/). The latest
stable release is v0.1.3 (see the repository
[tags](https://github.com/Ilinyh-org/caeproject/tags)).

## Quick start

### Parameters

Units-aware parameters (from `tests/unit/test_parameter.py`):

```python
from core.parameter import Parameter

p = Parameter(value=(2, "km"))
print(p.value)   # 2000 — converted to base units (m)
print(p.units)   # m
```

### Project with cases

Create a project, add cases, solve them concurrently and collect results
into a single DataFrame (from `tests/unit/test_project.py` and
`tests/e2e/test_project_full_workflow.py`):

```python
from caeproject import CAEProject

project = CAEProject.create_new(base_path=".", name="myproject")

case = project.create_case(name="case1")
# add tasks to the case, e.g. case.add_task(APDLTask(...))
project.solve(max_workers=2)

results = project.get_results()
print(results)  # pandas DataFrame with parameters and results of all cases
```

### Simple task

Prepare a task, solve it, get results:

```python
from caetask import APDLTask

task = APDLTask("test")
task.input_file = "test.inp"
task.results_files_names = ["text_file_from_ansys.dat"]
task.solve()

with open("text_file_from_ansys.dat") as file:
    print(file.readline())
```

### Multitask process

Run several tasks concurrently with `run_threads` — create tasks in one
call, solve them in another (see the tests in `tests/integration/` for
full working examples):

```python
from caetask import run_threads, APDLTask

def create_task(index):
    task = APDLTask("test")
    task.input_file = "test.inp"
    task.results_files_names = [f"task{index}_result.dat"]
    return task

tasks = run_threads(create_task, [0, 1, 2, 3, 4], max_workers=1)
run_threads(lambda task: task.solve(), tasks, max_workers=2)
```

### Rules

- Check all absolute and especially relative paths in input files.
- Relative paths work only if defined in the `additional_files`
  instance variable.
- The task-creation function has to be global.

## Tests

```
pytest -q -m "not solve"
```

Tests marked `solve` require heavy CAE solver backends.
