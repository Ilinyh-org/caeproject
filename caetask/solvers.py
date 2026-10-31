"""Concurrent execution helpers for running a task over data samples.

Provides :func:`run_processes` and :func:`run_threads`, which fan a
_callable task out over a list of samples with a process or thread
pool and print progress as tasks complete.
"""
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from threading import Lock

lock = Lock()
total_tasks = 0
completed = 0


def run_processes(task, data, max_workers=10):
    """Run ``task`` once per sample in a process pool.

    Each child process handles a single sample (``max_tasks_per_child=1``).
    Returns the results in completion order.
    """
    global total_tasks

    executor = ProcessPoolExecutor(max_workers=max_workers, max_tasks_per_child=1)
    results = []
    futures = [executor.submit(task, sample) for sample in data]
    total_tasks += len(futures)
    for future in as_completed(futures):
        future.add_done_callback(completed_callback)
        with lock:
            results.append(future.result())
    return results


def run_threads(task, data, max_workers=5):
    """Run ``task`` once per sample in a thread pool.

    Returns the results in completion order.
    """
    global total_tasks
    executor = ThreadPoolExecutor(max_workers=max_workers)
    results = []
    futures = [executor.submit(task, sample) for sample in data]
    total_tasks += len(futures)
    for future in as_completed(futures):
        future.add_done_callback(completed_callback)
        with lock:
            results.append(future.result())
    return results


def completed_callback(future):
    """Progress callback: count a finished task and print the backlog."""
    global completed, total_tasks
    with lock:
        completed += 1
        total_tasks -= 1
    print("task completed, tasks remaining: " +
          str(total_tasks))
