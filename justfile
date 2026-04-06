[private]
default:
    @just --list

set windows-shell := ["cmd.exe", "/c"]

# Run taplo, ruff, pytest, and basedpyright in check mode
check:
    uv run --group dev ruff check
    @just check-package packages/toolbox
    uv run --group dev basedpyright app tests
    uv run --group dev pytest -p terminalprogress tests
    uv run --group dev taplo fmt --check --diff pyproject.toml config-example.toml
    uv run --group dev ruff format --check
    uv run --group dev mdformat --number --wrap 80 --check *.md

[private]
check-package pkg:
    cd {{pkg}} && uv run basedpyright src tests
    cd {{pkg}} && uv run pytest -p terminalprogress tests
    cd {{pkg}} && uv run taplo fmt --check --diff pyproject.toml config-example.toml

# Run taplo, ruff's formatter, and ruff's isort rules in fix mode
format:
    uv run --group dev taplo fmt pyproject.toml packages/*/pyproject.toml config-example.toml
    uv run --group dev ruff format
    uv run --group dev ruff check --select I,RUF022,RUF023 --fix
    uv run --group dev mdformat --number --wrap 80 *.md

# Run taplo and ruff in fix mode
fix: format
    uv run --group dev ruff check --fix
