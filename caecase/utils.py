from datetime import datetime


CASE_DIR_FORMAT = "%Y_%m_%dT%H%M%S_%f"


def format_case_dir(dt=None):
    if dt is None:
        dt = datetime.now()
    return dt.strftime(CASE_DIR_FORMAT)


def parse_case_dir(name: str) -> datetime:
    return datetime.strptime(name, CASE_DIR_FORMAT)


def is_case_dir_name(name: str) -> bool:
    try:
        parse_case_dir(name)
        return True
    except ValueError:
        return False


