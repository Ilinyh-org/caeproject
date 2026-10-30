"""Helpers for timestamped CAE case directory names.

Case directories are named by a timestamp in :data:`CASE_DIR_FORMAT`
(e.g. ``2026_10_26T201530_123456``), sortable by creation time.
"""
from datetime import datetime

CASE_DIR_FORMAT = "%Y_%m_%dT%H%M%S_%f"


def format_case_dir(dt=None):
    """Format a datetime (default: now) as a case directory name."""
    if dt is None:
        dt = datetime.now()
    return dt.strftime(CASE_DIR_FORMAT)


def parse_case_dir(name: str) -> datetime:
    """Parse a case directory name back into a datetime.

    Raises:
        ValueError: if the name does not match the expected format.
    """
    return datetime.strptime(name, CASE_DIR_FORMAT)


def is_case_dir_name(name: str) -> bool:
    """Return True if the name is a valid case directory name."""
    try:
        parse_case_dir(name)
        return True
    except ValueError:
        return False


