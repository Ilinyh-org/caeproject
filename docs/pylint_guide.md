
## How to run pylint

We use **pylint** to check code quality.

Run this command from the project root:

```bash
pylint --recursive=y caetask
```

What this does:

*   `--recursive=y` – tells pylint to discover and check all Python modules and packages within the `caetask` directory, including subdirectories.
*   By default, pylint outputs a text report to your terminal and provides a score out of 10.

### Useful variations

You can customize the output or select specific files.

*   **To check a single file:**
    ```bash
    pylint caetask/some_module.py
    ```

*   **To disable the score or detailed reports:**
    ```bash
    pylint --recursive=y --score=no --reports=no caetask
    ```
    (By default, `--score` is `yes` and `--reports` is `no`).

*   **To output results in a different format (e.g., for CI):**
    ```bash
    pylint --recursive=y --output-format=json caetask > pylint_report.json
    ```
    Supported formats include `text`, `parseable`, `colorized`, `json`, `json2`, and `junit`.

---

## Where to find the HTML report

You can pipe pylint’s JSON output directly into the report generator:
```bash
pylint --recursive=y caetask | pylint_report > pylint_caetask_report.html
```

After running the command, open the generated file in your browser:

```
pylint_caetask_report.html
```