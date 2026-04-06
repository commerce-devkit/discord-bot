# Contributing

Thank you for improving DevKit Bot. This repository is a Commerce DevKit fork
of the upstream Ghostty Discord bot, so please keep changes focused, well
documented, and easy to reconcile with upstream when possible.

## Workflow

1. Create a semantic branch from `main`, for example
   `feature/commerce-devkit-bot-refactor`.
2. Make focused changes that follow the existing Python/uv project structure.
3. Use Conventional Commits for each commit.
4. Open a pull request against `main`.

## Commit conventions

Use the Conventional Commits format:

```text
<type>(<optional scope>): <description>
```

Common types in this repo:

- `feat`
- `fix`
- `docs`
- `refactor`
- `chore`
- `test`
- `ci`

## Local setup

This bot runs on Python 3.14+ and is managed with [uv].

1. Install [uv].
2. Copy `config-example.toml` to `config.toml`.
3. Fill in your Discord token, GitHub token, server IDs, role IDs, and channel
   IDs.
4. Optionally configure the `[docs]` section if you want the `/docs` command.
5. Run the bot:

   ```sh
   uv run -m app
   ```

## Configuration notes

Required config areas:

- `[tokens]` for Discord and GitHub credentials
- `[roles]` for mod/helper role IDs
- `[channels]` for help, log, media, showcase, and help-tag IDs
- `[webhook]` if you want GitHub webhook feeds

Important optional config areas:

- `[brand]` for user-facing bot/community naming
- `[github]` for the default repo, alias map, and ignored bot comment logins
- `[docs]` for enabling `/docs` with a configurable docs source

## Checks

If you have [just] installed, run:

```sh
just check
```

Otherwise run the equivalent manual checks:

```sh
uv run ruff check
uv run basedpyright app tests
uv run pytest -p terminalprogress tests
cd packages/toolbox
uv run basedpyright src tests
uv run pytest -p terminalprogress tests
```

## Project structure

- `app/` contains the Discord application and feature cogs.
- `packages/toolbox/` contains shared utilities used by the application.
- `tests/` contains application-level tests.

[just]: https://just.systems/
[uv]: https://docs.astral.sh/uv/
