# caetask

Run CAE applications from python script

What does this module do?
- create task object (e.g. APDL task), which is a combination of command script, parameters, options, etc.
- send task object to solve

Application is created to solve tasks in temporary folder of your os. But if you choose manual folder, this folder will be used

How to use this module in your script?
- prepare task
- solve task
- get results

Example:
APDL code of test.inp:
```
/batch
*dim,text,string,32,1
text(1)=\'test text from ansys\'
*cfopen,text_file_from_ansys,dat
*vwrite,text(1)
%C
*cfclos
```
Python script, that run the code:

```python

from caetask import APDLTask

task = APDLTask('test')
task.input_file = 'test.inp'
task.results_files_names = ["text_file_from_ansys.dat"]
task.solve()

with open('text_file_from_ansys.dat') as file:
    print(file.readline())
```
Output will be:

    test text from ansys


What should I do to run two tasks, one after another?
- Just create task, then solve in, and repeat for second task

How to run multitask process?
- first you need to pack your task creation code to local method with index or sample of input data as argument
- index used to identify sample of input data by it. Input data can be list, array, tuply, pandas frame etc.
- you can use global variable of input data

Example:
APDL code of test.inp:
```
/batch
parres,change,test,parm
*cfopen,task%num%_text_file,dat
*vwrite,num*3
%I
*cfclos
```
Python script, that run the code:

```python

from caetask import run_threads, APDLTask

input_data = (('1', 1), ('2', 2), ('3', 3), ('4', 4), ('5', 5))


def create_task(index):
    global input_data

    task_num = input_data[index][0]
    num_par = input_data[index][1]
    parm_file = "test" + task_num + ".parm"

    with open(parm_file, "w") as file:
        file.write("num=" + str(num_par))

    task = APDLTask('test')
    task.input_file = 'test.inp'
    task.parameters_file = parm_file
    task.results_files_names = ["task" + str(num_par) + "_text_file.dat"]
    return task


def solve_task(task):
    task.solve()


tasks = run_threads(create_task, [0, 1, 2, 3, 4], max_workers=2)
run_threads(solve_task, tasks, max_workers=2)

for index in [0, 1, 2, 3, 4]:
    num_par = input_data[index][1]
    with open("task" + str(num_par) + "_text_file.dat") as file:
        print(file.readline())
```
That code create 5 tasks and then solve them for two in a moment

Output will be:

    3
    6
    9
    12
    15

Rules:
- check all absolute and especially relative paths in input files
- relative paths will work only if you define them in additional_files instance variable
- create function has to be global