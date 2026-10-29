"""Filesystem helpers for CAE cases and projects.

Provides functions to create case directories and copy or write
files, plus :class:`FileManager` for project directories with
converter-based serialization and debounced async saving.
"""
import asyncio
import json
import random
import shutil
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from caecase.utils import format_case_dir
from caetask.default_registry import create_default_task_registry
from data_converter import ConverterRegistry


def create_case_dir(base_path: Path, name: str | None = None) -> Path:
    """Creates a unique timestamped directory."""
    while True:
        try:
            dir_name = name or format_case_dir()
            dir_path = base_path / dir_name
            dir_path.mkdir()

            return dir_path
        except FileExistsError:
            time.sleep(random.uniform(0.001, 0.01))


def add_files(
        files: Iterable[Path | str],
        target_path: Path
):
    """Copies external files into the case directory."""
    files_to_append = []
    for file in files:
        try:
            shutil.copy(file, target_path)
            files_to_append.append(file.name)
        except (FileNotFoundError, FileExistsError):
            print(f"Warning: File {file} not found.")
    return files_to_append


def save(
    data: str,
    path: Path,
    filename: str | None = None,
):
    """Write string ``data`` to ``path/filename`` on disk."""

    _write_to_disk(
        data,
        path,
        filename,
    )


def _write_to_disk(data: str,
                   path: Path,
                   filename: str | None = None):
    """Internal method to write JSON to disk."""
    save_path = path / f"{filename}"

    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(data)

    print(f"Data saved to {save_path}")


def load_from_disk(path: Path) -> dict[str, Any]:
    """Loads data from the default JSON file."""
    save_path = path / "case_data.json"
    if save_path.exists():
        with open(save_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


class FileManager:
    """File manager for a project directory.

    Tracks the files belonging to the project, resolves converters
    through a :class:`~data_converter.registry.ConverterRegistry`, and
    supports debounced asynchronous saving of dictionary data.
    """

    def __init__(self,
                 base_path: Path | None = None,
                 converter_registry: ConverterRegistry = None):
        self.base_path = base_path or Path.cwd()
        self._files = []

        # Save configuration
        self.save_delay = 2.0  # seconds
        self._save_task: asyncio.Task | None = None

        # Setup converter registry
        self.converter_registry = converter_registry or ConverterRegistry()
        self.converter_registry = create_default_task_registry()

    @staticmethod
    def create_project_dir(
            base_path: Path,
            name: str,
    ) -> Path:
        """Create (if needed) and return the project directory ``base_path/name``."""

        dir_name = name
        dir_path = base_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)

        return dir_path

    def schedule_save(self, data: dict[str, Any]):
        """Schedules a save operation with a delay (debouncing)."""
        if self._save_task:
            self._save_task.cancel()
        self._save_task = asyncio.create_task(self._delayed_save(data))

    async def _delayed_save(self, data: dict[str, Any]):
        """Waits for the delay, then writes to disk."""
        try:
            await asyncio.sleep(self.save_delay)
            _write_to_disk(data)
        except asyncio.CancelledError:
            pass  # Save was cancelled by a new update

    def save_immediately(self,
                         data: dict[str, Any],
                         path: Path,
                         format_type: str = 'json',
                         filename: str | None = None):
        """Forces an immediate write to disk, cancelling any pending saves."""
        converter = self.converter_registry.get(format_type)
        if self._save_task:
            self._save_task.cancel()
        _write_to_disk(data, path, converter, filename)

    @property
    def files(self) -> list[str]:
        """Names of the files currently tracked by the manager."""
        return self._files

    @files.setter
    def files(self, files: list[str]):
        self._files = files

