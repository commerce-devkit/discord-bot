import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, final, override
from urllib.parse import urlparse
from xml.etree import ElementTree

import discord as dc
import httpx
from discord.ext import commands, tasks
from loguru import logger

from app.config import config

if TYPE_CHECKING:
    from app.bot import GhosttyBot

_STATUS_URL_REGEX = re.compile(
    r"/(?P<account>[A-Za-z0-9_]+)/status(?:es)?/(?P<post_id>\d+)"
)


@dataclass(frozen=True, slots=True)
class FeedEntry:
    post_id: int
    link: str


def _strip_namespace(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _get_link(entry: ElementTree.Element) -> str | None:
    for child in entry:
        if _strip_namespace(child.tag) != "link":
            continue
        if href := child.get("href"):
            return href.strip()
        if child.text:
            return child.text.strip()
    return None


def parse_feed(feed: str) -> list[FeedEntry]:
    root = ElementTree.fromstring(feed)
    entries: list[FeedEntry] = []
    seen_post_ids: set[int] = set()

    if _strip_namespace(root.tag) == "rss":
        raw_entries = root.findall("./channel/item")
    elif _strip_namespace(root.tag) == "feed":
        raw_entries = [
            child for child in root if _strip_namespace(child.tag) == "entry"
        ]
    else:
        msg = f"unsupported feed root element: {_strip_namespace(root.tag)!r}"
        raise ValueError(msg)

    for entry in raw_entries:
        if not (link := _get_link(entry)):
            continue
        if not (match := _STATUS_URL_REGEX.search(urlparse(link).path)):
            continue
        post_id = int(match["post_id"])
        if post_id in seen_post_ids:
            continue
        seen_post_ids.add(post_id)
        entries.append(FeedEntry(post_id=post_id, link=link))

    return sorted(entries, key=lambda entry: entry.post_id)


def format_post_link(link: str, fallback_account: str) -> str:
    if match := _STATUS_URL_REGEX.search(urlparse(link).path):
        account = match["account"]
        post_id = match["post_id"]
    else:
        post_id_match = re.search(
            r"/status(?:es)?/(?P<post_id>\d+)", urlparse(link).path
        )
        if post_id_match is None:
            return link
        account = fallback_account
        post_id = post_id_match["post_id"]

    return f"https://fxtwitter.com/{account}/status/{post_id}"


def select_new_entries(
    entries: list[FeedEntry], last_post_id: int | None
) -> tuple[list[FeedEntry], int | None]:
    if not entries:
        return [], last_post_id

    newest_post_id = entries[-1].post_id
    if last_post_id is None:
        return [], newest_post_id

    return [entry for entry in entries if entry.post_id > last_post_id], newest_post_id


@final
class TwitterFeed(commands.Cog):
    def __init__(self, bot: GhosttyBot) -> None:
        self.bot = bot
        twitter_feed = config().twitter_feed
        assert twitter_feed is not None
        self.twitter_feed = twitter_feed
        self.state_path = config().data_dir / "twitter-feed-state.json"
        self.last_post_id = self._load_state()
        self.poll_feed.change_interval(minutes=twitter_feed.poll_interval_minutes)
        self.poll_feed.start()

    @override
    async def cog_unload(self) -> None:
        self.poll_feed.cancel()

    def _load_state(self) -> int | None:
        if not self.state_path.exists():
            return None
        raw_state = json.loads(self.state_path.read_text())
        if raw_state["last_post_id"] is None:
            return None
        return int(raw_state["last_post_id"])

    def _save_state(self) -> None:
        self.state_path.write_text(json.dumps({"last_post_id": self.last_post_id}))

    async def _fetch_entries(self) -> list[FeedEntry]:
        async with httpx.AsyncClient(
            follow_redirects=True,
            headers={"User-Agent": "commerce-devkit-discord-bot/0.1"},
            timeout=20.0,
        ) as client:
            response = await client.get(self.twitter_feed.resolved_feed_url)
            response.raise_for_status()
        return parse_feed(response.text)

    def _media_channel(self) -> dc.TextChannel:
        channel = self.bot.get_channel(config().channel_ids.media)
        assert isinstance(channel, dc.TextChannel)
        return channel

    @tasks.loop(minutes=5)
    async def poll_feed(self) -> None:
        entries = await self._fetch_entries()
        new_entries, newest_post_id = select_new_entries(entries, self.last_post_id)
        if newest_post_id is None:
            return

        if self.last_post_id is None:
            self.last_post_id = newest_post_id
            self._save_state()
            logger.info(
                "initialized twitter feed for @{account} at post {post_id}",
                account=self.twitter_feed.account,
                post_id=newest_post_id,
            )
            return

        media_channel = self._media_channel()
        for entry in new_entries:
            await media_channel.send(
                format_post_link(entry.link, self.twitter_feed.account),
                suppress_embeds=False,
            )
            self.last_post_id = entry.post_id
            self._save_state()

    @poll_feed.before_loop
    async def before_poll_feed(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: GhosttyBot) -> None:
    twitter_feed = config().twitter_feed
    if twitter_feed is None:
        logger.info("twitter feed component disabled; no twitter_feed configuration")
        return

    logger.info(
        "twitter feed component enabled for @{account}",
        account=twitter_feed.account,
    )
    await bot.add_cog(TwitterFeed(bot))
