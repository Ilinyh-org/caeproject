# Installing the package (using pyproject.toml)

This project uses **pyproject.toml** for dependency management.

There are two main ways to install it:
normal (runtime only) and development (with tools for contributors).

---

## 1. Normal installation (for users)

This installs only the packages required to run the application.

From the project root, run:

```
pip install .
```

If you want an editable install (changes apply immediately without reinstall):

```
pip install -e .
```

Use this when you only need the app to run, not develop it.

---

## 2. Development installation (for contributors)

Development installation includes extra tools such as:
 
* pytest
* linters (flake8, ruff, etc.)
* formatters (black, isort)
* coverage tools

Install with:

```
pip install -e ".[dev]"
```

The `[dev]` section is defined in `pyproject.toml` under:

```
[project.optional-dependencies]
dev = [
    ...
]
```

Use this if you are going to write code or tests.

---

## 3. Recommended: use a virtual environment

Always install inside a virtual environment:

```
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
.venv\Scripts\activate      # Windows

pip install -e ".[dev]"
```

---

## Summary

| Goal             | Command                   |
| ---------------- | ------------------------- |
| Run app only     | `pip install .`           |
| Develop + test   | `pip install -e ".[dev]"` |
| Editable runtime | `pip install -e .`        |

---

If something fails, upgrade pip first:

```
pip install --upgrade pip
```
