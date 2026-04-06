import datetime as dt
import json
from typing import TYPE_CHECKING, NotRequired, Self, TypedDict, cast, final, override

import discord as dc
from discord.app_commands import Choice  # noqa: TC002
from discord.ext import commands
from githubkit.exception import RequestFailed
from loguru import logger

from app.config import config, gh
from toolbox.discord import generate_autocomplete
from toolbox.message_moving import get_or_create_webhook

if TYPE_CHECKING:
    from collections.abc import Iterable

    from app.bot import GhosttyBot
    from app.config import ConfigDocs


class Entry(TypedDict):
    type: str
    path: str
    children: NotRequired[list[Self]]


@final
class Docs(commands.Cog):
    docs_config: ConfigDocs
    sitemap: dict[str, list[str]]

    def __init__(self, bot: GhosttyBot) -> None:
        self.bot = bot
        docs_config = config().docs
        assert docs_config is not None
        self.docs_config = docs_config
        self.sitemap = {}

    @override
    async def cog_load(self) -> None:
        try:
            await self.refresh_sitemap()
        except RequestFailed:
            logger.warning(
                "refreshing sitemap failed, running bot with limited functionality"
            )

    @dc.app_commands.command(name="docs", description="Link a documentation page.")
    @dc.app_commands.guild_only()
    async def docs(
        self, interaction: dc.Interaction, section: str, page: str, message: str = ""
    ) -> None:
        try:
            if not message or not isinstance(
                interaction.channel, dc.TextChannel | dc.ForumChannel
            ):
                await interaction.response.send_message(
                    self.get_docs_link(section, page)
                )
                return
            webhook = await get_or_create_webhook(interaction.channel)
            await webhook.send(
                f"{message}\n{self.get_docs_link(section, page)}",
                username=interaction.user.display_name,
                avatar_url=interaction.user.display_avatar.url,
            )
            await interaction.response.send_message(
                "Documentation linked.", ephemeral=True
            )
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
        except dc.HTTPException:
            await interaction.response.send_message(
                "Message content too long.", ephemeral=True
            )

    def _load_children(
        self, sitemap: dict[str, list[str]], path: str, children: list[Entry]
    ) -> None:
        sitemap[path] = []
        for item in children:
            sitemap[path].append((page := item["path"].lstrip("/")) or "overview")
            if item["type"] == "folder":
                self._load_children(sitemap, f"{path}-{page}", item.get("children", []))

    async def _get_file(self, path: str) -> str:
        docs_config = self.docs_config
        return (
            await gh().rest.repos.async_get_content(
                docs_config.source_owner,
                docs_config.source_repo,
                path,
                headers={"Accept": "application/vnd.github.raw+json"},
            )
        ).text

    @dc.app_commands.command(name="refresh-docs", description="Refresh sitemap docs.")
    @dc.app_commands.guild_only()
    # Hide interaction from non-mods
    @dc.app_commands.default_permissions(ban_members=True)
    async def refresh_docs(self, interaction: dc.Interaction) -> None:
        # The client-side check with `default_permissions` isn't guaranteed to work.
        if not config().is_mod(interaction.user):
            await interaction.response.send_message(
                "Only mods can run this command", ephemeral=True
            )
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        await self.refresh_sitemap()
        await interaction.followup.send("Sitemap refreshed.", ephemeral=True)

    async def refresh_sitemap(self) -> None:
        docs_config = self.docs_config
        nav: list[Entry] = json.loads(await self._get_file(docs_config.nav_path))[
            "items"
        ]
        nav_entries: dict[str, list[str]] = {}
        for entry in nav:
            if entry["type"] != "folder":
                continue
            self._load_children(
                nav_entries, entry["path"].lstrip("/"), entry.get("children", [])
            )

        self.sitemap.clear()
        for key, nav_path in docs_config.nav_sections.items():
            if nav_path not in nav_entries:
                logger.warning(
                    "docs nav path {path!r} missing for section {section!r}",
                    path=nav_path,
                    section=key,
                )
                continue
            self.sitemap[key] = nav_entries[nav_path]

        for key, config_path in docs_config.page_sources.items():
            self.sitemap[key] = [
                line.removeprefix("## ").strip("`")
                for line in (await self._get_file(config_path)).splitlines()
                if line.startswith("## ")
            ]
        self.bot.bot_status.last_sitemap_refresh = dt.datetime.now(tz=dt.UTC)

    @docs.autocomplete("section")
    async def section_autocomplete(
        self, _: dc.Interaction, current: str
    ) -> list[Choice[str]]:
        return generate_autocomplete(current, self.docs_config.url_paths)

    @docs.autocomplete("page")
    async def page_autocomplete(
        self, interaction: dc.Interaction, current: str
    ) -> list[Choice[str]]:
        if not interaction.data:
            return []
        options = cast(
            "Iterable[dict[str, str]] | None", interaction.data.get("options")
        )
        if not options:
            return []
        section = next(
            (opt["value"] for opt in options if opt["name"] == "section"),
            None,
        )
        if section is None:
            return []
        return generate_autocomplete(current, self.sitemap.get(section, []))

    def get_docs_link(self, section: str, page: str) -> str:
        if section not in self.docs_config.url_paths:
            msg = f"Invalid section {section!r}"
            raise ValueError(msg)
        if page not in self.sitemap.get(section, []):
            msg = f"Invalid page {page!r}"
            raise ValueError(msg)
        return (
            self.docs_config.base_url.rstrip("/")
            + "/"
            + self.docs_config.url_paths[section]
            + (page if page != "overview" else "")
        )


async def setup(bot: GhosttyBot) -> None:
    if config().docs is None:
        logger.info("docs component disabled; no docs configuration provided")
        return
    await bot.add_cog(Docs(bot))
