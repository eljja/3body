# Development Guide

## Environment

This project currently targets Python 3.11+.

Install dependencies:

```powershell
& 'D:\Codex\.venv\Scripts\python.exe' -m pip install -e .[dev] --no-build-isolation
```

Run tests:

```powershell
& 'D:\Codex\.venv\Scripts\python.exe' -m pytest
```

Run the app:

```powershell
& 'D:\Codex\.venv\Scripts\python.exe' -m streamlit run src/threebody/ui/app.py
```

## Recommended Workflow

1. Validate solver behavior against the analytic two-body baseline.
2. Add or refine structured restricted three-body experiments.
3. Extend general three-body diagnostics only with benchmark coverage.
4. Add compact models only after declaring the target regime and error metric.

## Testing Standard

Any new solver or model should be accompanied by at least one of:

- analytic comparison,
- invariant drift threshold,
- literature benchmark reproduction,
- or explicit regression test on a named orbit family.

## Git Workflow

The local repository uses `main` as the primary branch.
The GitHub remote is `https://github.com/eljja/3body.git`.
Keep feature work on short-lived topic branches or scoped commits and merge back only after tests pass.
When changing public-facing claims, update the relevant documentation and run the static artifact verifier before deployment.
