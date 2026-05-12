import json
from pathlib import Path

class Serializable:
    CONFIG_DEFAULT_NAME = "config.json"

    def to_dict(self) -> dict:
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data: dict):
        raise NotImplementedError

    def save_config(self, config_path: Path):
        if config_path.is_dir():
            config_path = config_path / self.CONFIG_DEFAULT_NAME

        with open(config_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_config(cls, config_path: Path, **kwargs):
        if config_path.is_dir():
            config_path = config_path / cls.CONFIG_DEFAULT_NAME

        with open(config_path, "r") as f:
            data = json.load(f)

        return cls.from_dict(data, **kwargs)