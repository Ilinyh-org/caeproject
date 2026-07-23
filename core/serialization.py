import json
from pathlib import Path
from typing import Any


class Serializable:
    CONFIG_DEFAULT_NAME = "config.json"

    def __init__(
            self,
            base_path: Path | None = None,
            name: str | None = None,
    ):
        self.base_path = base_path
        self.name = name

    @property
    def path(self) -> Path:
        return self.base_path / self.name

    def to_dict(self) -> dict:
        return {
            "name": self.name
        }

    @classmethod
    def from_dict(
            cls,
            data: dict,
            base_path: Path | str | None,
            name: str | None
    ):
        raise NotImplementedError

    def save_config(self, directory: Path | None = None):
        if directory is None:
            directory = self.path

        if not directory.is_dir():
            raise NotADirectoryError(f"Ожидалась директория конфигурации, но получен файл: {directory}")

        config_file = directory / self.CONFIG_DEFAULT_NAME

        with open(config_file, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_config(
            cls,
            config_path: Path | str | None = None,
    ):
        if isinstance(config_path, str):
            config_path = Path(config_path)

        if config_path.is_dir():
            config_path /= cls.CONFIG_DEFAULT_NAME

        with open(config_path, "r") as f:
            data = json.load(f)

        config_folder_path = config_path.parent

        base_path = config_folder_path.parent
        name = config_folder_path.name

        return cls.from_dict(
            data,
            base_path=base_path,
            name=name
        )

    @staticmethod
    def serialize(
            value: Any,
            relative_to: Path | None = None
    ):
        if isinstance(value, Path):
            if (
                    relative_to is not None
                    and value.is_relative_to(relative_to.absolute())
            ):
                value = value.relative_to(relative_to.absolute())
            return str(value)

        return value

    @staticmethod
    def normalize_path(path: str | Path | None) -> Path:
        if path is None:
            return Path.cwd()

        if isinstance(path, str):
            return Path(path)

        if isinstance(path, Path):
            return path

        raise TypeError(f"Expected str, Path or None, got {type(path).__name__}")
