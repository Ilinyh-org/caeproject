import json
from pathlib import Path


def serialize(
        value,
        relative_to: Path | None = None
):
    if isinstance(value, Path):
        if relative_to is not None:
            return str(
                value.relative_to(relative_to)
            )
        return str(value)

    return value


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
    def load_config(
            cls,
            config_path: Path | None = None,
            **kwargs
    ):
        if not config_path.is_dir():
            raise NotADirectoryError(f"Ожидалась директория конфигурации, но получен файл: {config_path}")

        with open(config_path / cls.CONFIG_DEFAULT_NAME, "r") as f:
            data = json.load(f)

        if not "base_path" in kwargs:
            kwargs['base_path'] = config_path.parent
        if not "name" in kwargs:
            kwargs['name'] = config_path.name

        return cls.from_dict(data, **kwargs)