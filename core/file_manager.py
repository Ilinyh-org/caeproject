
import asyncio
import json
import shutil
import random
import datetime
from pathlib import Path
from typing import Any, Dict, Iterable
import time

from core.converter import JSONConverter, DataConverter, APDLConverter, SchemeConverter
from core.converter_registry import ConverterRegistry


class FileManager:
    def __init__(self, base_path: Path = None, converter_registry: ConverterRegistry = None):
        self.base_path = base_path or Path.cwd()
        self.case_dir = self._create_case_dir()
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


    def _create_case_dir(self) -> Path:
        """Creates a unique timestamped directory."""
        while True:
            try:
                dir_name = datetime.datetime.now().strftime("%Y_%m_%dT%H%M%S_%f")
                dir_path = self.base_path / dir_name
                dir_path.mkdir()
                return dir_path
            except FileExistsError:
                time.sleep(random.uniform(0.001, 0.01))

    def add_files(self, files: Iterable[Path | str]):
        """Copies external files into the case directory."""
        for file in files:
            try:
                shutil.copy(file, self.case_dir)
                self._files.append(file)
            except (FileNotFoundError, FileExistsError):
                print(f"Warning: File {file} not found.")

    def get_file_path(self, filename: str) -> Path:
        """Returns the full path to a file inside the case directory."""
        return self.case_dir / filename

    def schedule_save(self, data: Dict[str, Any]):
        """Schedules a save operation with a delay (debouncing)."""
        if self._save_task:
            self._save_task.cancel()
        self._save_task = asyncio.create_task(self._delayed_save(data))

    async def _delayed_save(self, data: Dict[str, Any]):
        """Waits for the delay, then writes to disk."""
        try:
            await asyncio.sleep(self.save_delay)
            self._write_to_disk(data)
        except asyncio.CancelledError:
            pass  # Save was cancelled by a new update

    def save_immediately(self, data: Dict[str, Any], format_type: str = 'json', filename: str = None):
        """Forces an immediate write to disk, cancelling any pending saves."""
        converter = self.converter_registry.get(format_type)
        if self._save_task:
            self._save_task.cancel()
        self._write_to_disk(data, converter, filename)

    def _write_to_disk(self, data: Dict[str, Any], converter: DataConverter, filename: str = None):
        """Internal method to write JSON to disk."""
        base_filename = filename if filename else "case_data"

        extension = converter.get_extension()

        save_path = self.case_dir / f"{base_filename}.{extension}"

        # Convert data to string
        content = converter.convert(data)

        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"Data saved to {save_path}")

    def load_from_disk(self) -> Dict[str, Any]:
        """Loads data from the default JSON file."""
        save_path = self.case_dir / "case_data.json"
        if save_path.exists():
            with open(save_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    @property
    def files(self) -> list[str]:
        return self._files

    @files.setter
    def files(self, files: list[str]):
        self._files = files

    @property
    def case_dir(self) -> Path:
        return self._case_dir

    @case_dir.setter
    def case_dir(self, case_dir: Path):
        self._case_dir = case_dir