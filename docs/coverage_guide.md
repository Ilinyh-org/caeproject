
## How to run coverage

We use **pytest** together with **pytest-cov**.

Run this command from the project root:

```bash
pytest --cov=caetask --cov-report=term-missing --cov-report=html
```

What this does:

* `--cov=caetask` – measure coverage for the `caetask` package
* `--cov-report=term-missing` – show missing lines in the terminal
* `--cov-report=html` – generate an HTML report

---

## Where to find the HTML report

After running the command, a folder will be created:

```
htmlcov/
```

Open this file in your browser:

```
htmlcov/index.html
```

