# DevKit Bot

DevKit Bot is the Commerce DevKit Discord bot, adapted from the upstream
[ghostty-org/discord-bot](https://github.com/ghostty-org/discord-bot) project.
This fork keeps the upstream component structure where practical so future bug
fixes remain easier to adopt, while replacing Ghostty-specific assumptions with
Commerce DevKit-focused configuration.

For development setup and project structure, see
[CONTRIBUTING.md](CONTRIBUTING.md).

## Features

- Help-post moderation via `/close`
- Automatic stale/solved handling for the `#help` forum
- GitHub issue, PR, discussion, commit, comment, and code-link expansion
- Social embed fixups
- Optional Twitter/X feed posting into `#media`
- Message filters for showcase/media-style channels
- Message moving and follow-up editing tools
- XKCD mention support
- Optional `/docs` links when a docs source is configured

## Twitter/X feed integration

The bot can optionally post new updates from a configured Twitter/X account into
the configured `#media` channel.

Configure the optional `[twitter_feed]` section in `config.toml`:

```toml
[twitter_feed]
account = "CommerceDevKit"
feed_url = "https://nitter.net/{account}/rss"
poll_interval_minutes = 5
```

- `account` is the handle to follow.
- `feed_url` is a configurable source URL and may include `{account}`.
- `poll_interval_minutes` controls how often the bot checks for new posts.

On the first successful sync, the bot records the newest post and starts posting
only newer items after that, so enabling the integration does not backfill old
posts into `#media`.

## GitHub mentions

The bot expands GitHub-like mentions such as `#123`, `web#45`, or
`commerce-devkit/website#45`.

- Bare mentions like `#123` resolve against the configured default repo.
- Short aliases resolve against the configured GitHub owner and alias map.
- Full `owner/repo#123` and GitHub URLs also work.

The default example configuration targets the `commerce-devkit` GitHub
organization and uses `website` as the default repo for bare mentions.

## Forking and attribution

This repository is an adapted fork of the upstream Ghostty Discord bot. Please
keep that attribution intact when making further customizations, and prefer
localized config- or component-level changes over broad rewrites so upstream
improvements stay easier to merge or cherry-pick later.
