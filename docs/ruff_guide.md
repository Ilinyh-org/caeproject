# Ruff guide

This project uses **ruff** as a fast Python linter and formatter. This is a simple guide on how to run it locally, in the same spirit as the pylint workflow (`.github/workflows/pylint.yml`).

## Install

```bash
pip install ruff
```

## Run the linter

From the project root:

```bash
ruff check .
```

What this does:

* checks every Python file in the project for lint errors
* reports rule codes (for example `E501` – line too long)

## Auto-fix problems

Ruff can fix many findings automatically:

```bash
ruff check --fix .
```

## Format the code

Ruff also includes a formatter (a drop-in replacement for black):

```bash
ruff format .
```

## Useful options

* `ruff check . --output-format=full` – show more detailed messages
* `ruff check path/to/file.py` – lint a single file or directory
* `ruff rule E501` – show the documentation for a specific rule
* `ruff clean` – remove the ruff cache

## Configuration

Ruff can be configured in `pyproject.toml` under the `[tool.ruff]` section, for example:

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W"]
```

The project does not currently ship a ruff configuration, so ruff runs with its defaults.
