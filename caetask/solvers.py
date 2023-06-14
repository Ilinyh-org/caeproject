from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor
from threading import Lock

lock = Lock()
total_tasks = 0
completed = 0


def run_processes(task, data, max_workers=10):
    global completed, total_tasks
    executor = ProcessPoolExecutor(max_workers=max_workers)
    results = []
    futures = [executor.submit(task, sample) for sample in data]
    total_tasks = len(futures)
    for future in as_completed(futures):
        future.add_done_callback(completed_callback)
        with lock:
            results.append(future.result())
    return results


def run_threads(task, data, max_workers=5):
    global completed, total_tasks
    executor = ThreadPoolExecutor(max_workers=max_workers)
    results = []
    futures = [executor.submit(task, sample) for sample in data]
    total_tasks = len(futures)
    for future in as_completed(futures):
        future.add_done_callback(completed_callback)
        with lock:
            results.append(future.result())
    return results


def completed_callback(future):
    global completed, total_tasks, lock
    with lock:
        completed += 1
    print("завершена задача, осталось задач: " +
          str(total_tasks - completed))
