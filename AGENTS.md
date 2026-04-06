# Agent Guidelines

## Purpose

This repository contains the Commerce DevKit Discord bot, adapted from the
upstream Ghostty Discord bot. Agents contributing here should preserve clear
upstream attribution, keep changes maintainable, and avoid unnecessary
divergence from upstream structure.

## Repository overview

- Python project managed with `uv`
- Main bot application in `/app`
- Shared utilities in `/packages/toolbox`
- Tests in `/tests`
- Example runtime configuration in `/config-example.toml`
- Checks orchestrated by `/justfile`

## General guidelines

- Prefer clarity over cleverness
- Keep changes focused and easy to review
- Follow existing component and utility patterns before adding new abstractions
- Favor configuration seams over hard-coded Commerce DevKit logic when that
  improves future upstream compatibility
- Preserve explicit credit to the upstream Ghostty repository

## Bot-specific practices

- New Discord features should usually live in `app/components/`
- Shared helpers should go in `packages/toolbox/` only when they are genuinely
  reusable
- If a feature is Commerce DevKit-specific, prefer isolating it in config or a
  dedicated cog instead of reshaping shared infrastructure
- Treat upstream behavior as a dependency: adapt locally, but do not rewrite
  large stable subsystems without a clear need
- Do not reintroduce dropped Ghostty-only features such as the old invite flow,
  HCB feed, or Zig highlighting without explicit direction

## Validation

Prefer:

```bash
just check
```

If `just` is unavailable, run the equivalent manual checks:

```bash
uv run --group dev ruff check
uv run --group dev basedpyright app tests
uv run --group dev pytest -p terminalprogress tests
cd packages/toolbox
uv run basedpyright src tests
uv run pytest -p terminalprogress tests
```

## Branch and commit conventions

- Create semantic branch names such as `feature/<short-description>` or
  `docs/<short-description>`
- Use Conventional Commits:

  ```text
  <type>(<optional scope>): <short summary>
  ```

- Prefer small, focused commits over one large mixed commit
- Keep documentation-only changes in their own commit when practical

## What to avoid

- Vague commits or mixed unrelated changes
- Hard-coding Commerce DevKit repo assumptions in multiple places when config
  can hold them once
- Removing upstream attribution
- Adding new build or lint tooling without a strong reason
