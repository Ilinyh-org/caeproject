
import asyncio
import json
import shutil
import random
from pathlib import Path
from typing import Any, Dict, Iterable
import time

from caecase.utils import format_case_dir
from core.converter import JSONConverter, DataConverter, APDLConverter, SchemeConverter
from core.converter_registry import ConverterRegistry


def _write_to_disk(data: Dict[str, Any],
                   path: Path,
                   converter: DataConverter,
                   filename: str = None):
    """Internal method to write JSON to disk."""
    base_filename = filename if filename else "case_data"

    extension = converter.get_extension()

    save_path = path / f"{base_filename}.{extension}"

    # Convert data to string
    content = converter.convert(data)

    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Data saved to {save_path}")


def load_from_disk(path: Path) -> Dict[str, Any]:
    """Loads data from the default JSON file."""
    save_path = path / "case_data.json"
    if save_path.exists():
        with open(save_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


class FileManager:
    def __init__(self,
                 base_path: Path = None,
                 converter_registry: ConverterRegistry = None):
        self.base_path = base_path or Path.cwd()
        self._files = []

        # Save configuration
        self.save_delay = 2.0  # seconds
        self._save_task: asyncio.Task | None = None

        # Setup converter registry
        self.converter_registry = converter_registry or ConverterRegistry()
        if not self.converter_registry.list_formats():
            # Register default converters
            self.converter_registry.register('json', JSONConverter())
            self.converter_registry.register('APDL', APDLConverter())
            self.converter_registry.register('Scheme', SchemeConverter())

    @staticmethod
    def create_project_dir(
            base_path: Path,
            name: str,
    ) -> Path:

        dir_name = name
        dir_path = base_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)

        return dir_path

    @staticmethod
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

    @staticmethod
    def add_files(
            files: Iterable[Path | str],
            target_path: Path
    ):
        """Copies external files into the case directory."""
        files_to_append = []
        for file in files:
            try:
                shutil.copy(file, target_path)
                files_to_append.append(file)
            except (FileNotFoundError, FileExistsError):
                print(f"Warning: File {file} not found.")
        return files_to_append

    def schedule_save(self, data: Dict[str, Any]):
        """Schedules a save operation with a delay (debouncing)."""
        if self._save_task:
            self._save_task.cancel()
        self._save_task = asyncio.create_task(self._delayed_save(data))

    async def _delayed_save(self, data: Dict[str, Any]):
        """Waits for the delay, then writes to disk."""
        try:
            await asyncio.sleep(self.save_delay)
            _write_to_disk(data)
        except asyncio.CancelledError:
            pass  # Save was cancelled by a new update

    def save_immediately(self,
                         data: Dict[str, Any],
                         path: Path,
                         format_type: str = 'json',
                         filename: str = None):
        """Forces an immediate write to disk, cancelling any pending saves."""
        converter = self.converter_registry.get(format_type)
        if self._save_task:
            self._save_task.cancel()
        _write_to_disk(data, path, converter, filename)

    @staticmethod
    def save(
        data: Dict[str, Any],
        path: Path,
        format_type: str = "json",
        filename: str = None,
    ):

        registry = ConverterRegistry.create_default_registry()
        converter = registry.get(format_type)

        _write_to_disk(
            data,
            path,
            converter,
            filename,
        )

    @property
    def files(self) -> list[str]:
        return self._files

    @files.setter
    def files(self, files: list[str]):
        self._files = files

