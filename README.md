# CAETask

Run CAE applications from python script

What does this module do?
- create task object
- send task object to solve
- 

can we solve a task not in temperary folder?
yes, but this is stupid
if we choose temperary folder by manual, then we use this folder, otherwise we use temperary folders

How to use this module in your script?
- prepare task
- solve task
- get results


How to run multitask process?
- first you need to pack your task creation code to local method with index as argument
- index used to identify sample of input data by it. Input data can be list, array, tuply, pandas frame etc.
- you can use global variable of input data
- 
But what should I do to run two tasks, one after another?
Just create task, then solve in, and repeat for second task

rules:
- check all absolute and especially relative paths in input files
- relative paths will work only if you define them in additional_files instance variable
- create function has to be global