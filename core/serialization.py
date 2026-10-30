"""JSON serialization support for objects with a base path and a name.

Provides the :class:`Serializable` base class, which saves an object's
configuration as a JSON file inside its own directory and restores it,
plus small helpers for path handling during (de)serialization.
"""
import json
from pathlib import Path
from typing import Any


class Serializable:
    """Base class for objects whose configuration can be saved to and
    loaded from a ``config.json`` file inside their own directory.

    Subclasses should extend :meth:`to_dict` and implement
    :meth:`from_dict` to serialize their additional state.
    """

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
        """Full path of the object's own directory (``base_path / name``)."""
        return self.base_path / self.name

    def to_dict(self) -> dict:
        """Return the object's state as a JSON-serializable dict.

        Returns:
            dict: Dict with the ``name`` field; subclasses extend it.
        """
        return {
            "name": self.name
        }

    @classmethod
    def from_dict(
            cls,
            data: dict,
            *,
            base_path: Path | None = None,
            name: str | None = None
    ):
        """Create an instance from its dict representation.

        Args:
            data (dict): Dict previously produced by :meth:`to_dict`.
            base_path (Path | None): Base directory of the object.
            name (str | None): Name of the object's own directory.

        Raises:
            NotImplementedError: Always; subclasses must override.
        """
        raise NotImplementedError

    def save_config(self, directory: Path | None = None):
        """Save the object's configuration as JSON.

        Writes :meth:`to_dict` output to ``config.json`` inside
        ``directory`` (defaults to :attr:`path`).

        Args:
            directory (Path | None): Directory to write the config into.

        Raises:
            NotADirectoryError: If the target path is not a directory.
        """
        if directory is None:
            directory = self.path

        if not directory.is_dir():
            raise NotADirectoryError(f"Expected a configuration directory, "
                                     f"but got a file: {directory}")

        config_file = directory / self.CONFIG_DEFAULT_NAME

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_config(
            cls,
            config_path: Path | str | None = None,
    ):
        """Load a configuration and build an instance from it.

        If ``config_path`` is a directory, ``config.json`` inside it is
        read. The base path and name are inferred from the config
        location (the folder holding the config file and its parent),
        then passed to :meth:`from_dict`.

        Args:
            config_path (Path | str | None): Path to the config file or
                to the directory containing it.
        """
        if isinstance(config_path, str):
            config_path = Path(config_path)

        if config_path.is_dir():
            config_path /= cls.CONFIG_DEFAULT_NAME

        with open(config_path, "r", encoding="utf-8") as f:
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
        """Convert a value into a JSON-friendly form.

        Paths are returned as strings; when the path lies inside
        ``relative_to``, it is first made relative to it.

        Args:
            value (Any): Value to serialize.
            relative_to (Path | None): Base directory for relative paths.

        Returns:
            Any: The serialized value (string for paths, otherwise
            unchanged).
        """
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
        """Normalize a path value to a ``Path``.

        Args:
            path (str | Path | None): ``None`` means the current working
                directory; strings are converted to ``Path``.

        Returns:
            Path: The normalized path.

        Raises:
            TypeError: If the value is not ``str``, ``Path`` or ``None``.
        """
        if path is None:
            return Path.cwd()

        if isinstance(path, str):
            return Path(path)

        if isinstance(path, Path):
            return path

        raise TypeError(f"Expected str, Path or None, got {type(path).__name__}")
