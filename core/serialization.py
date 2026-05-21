import json
from pathlib import Path

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
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data: dict):
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
    def load_config(cls, config_path: Path, **kwargs):
        if not config_path.is_dir():
            raise NotADirectoryError(f"Ожидалась директория конфигурации, но получен файл: {config_path}")

        with open(config_path / cls.CONFIG_DEFAULT_NAME, "r") as f:
            data = json.load(f)

        return cls.from_dict(data, **kwargs)