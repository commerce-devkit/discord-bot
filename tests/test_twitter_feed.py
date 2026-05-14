import pytest

from app.components.twitter_feed import (
    FeedEntry,
    format_post_link,
    parse_feed,
    select_new_entries,
)
from app.config import ConfigTwitterFeed

RSS_FEED = """\
<rss version="2.0">
  <channel>
    <title>Commerce DevKit</title>
    <item>
      <title>Newest</title>
      <link>https://nitter.net/CommerceDevKit/status/200</link>
    </item>
    <item>
      <title>Older</title>
      <link>https://twitter.com/CommerceDevKit/status/100</link>
    </item>
    <item>
      <title>Duplicate</title>
      <link>https://x.com/CommerceDevKit/status/200</link>
    </item>
    <item>
      <title>Ignored</title>
      <link>https://example.com/not-a-post</link>
    </item>
  </channel>
</rss>
"""

ATOM_FEED = """\
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Atom post</title>
    <link href="https://x.com/CommerceDevKit/status/300" />
  </entry>
</feed>
"""


def test_parse_feed_supports_rss_and_deduplicates() -> None:
    assert parse_feed(RSS_FEED) == [
        FeedEntry(post_id=100, link="https://twitter.com/CommerceDevKit/status/100"),
        FeedEntry(post_id=200, link="https://nitter.net/CommerceDevKit/status/200"),
    ]


def test_parse_feed_supports_atom() -> None:
    assert parse_feed(ATOM_FEED) == [
        FeedEntry(post_id=300, link="https://x.com/CommerceDevKit/status/300")
    ]


def test_parse_feed_rejects_unknown_root() -> None:
    with pytest.raises(ValueError, match="unsupported feed root element"):
        parse_feed("<html></html>")


def test_format_post_link_uses_fxtwitter() -> None:
    assert (
        format_post_link(
            "https://nitter.net/CommerceDevKit/status/200", "fallback_user"
        )
        == "https://fxtwitter.com/CommerceDevKit/status/200"
    )


def test_format_post_link_falls_back_to_configured_account() -> None:
    assert (
        format_post_link("https://example.com/status/200", "CommerceDevKit")
        == "https://fxtwitter.com/CommerceDevKit/status/200"
    )


def test_select_new_entries_skips_initial_backfill() -> None:
    entries = [
        FeedEntry(post_id=100, link="https://x.com/CommerceDevKit/status/100"),
        FeedEntry(post_id=200, link="https://x.com/CommerceDevKit/status/200"),
    ]

    assert select_new_entries(entries, None) == ([], 200)


def test_select_new_entries_returns_only_newer_posts() -> None:
    entries = [
        FeedEntry(post_id=100, link="https://x.com/CommerceDevKit/status/100"),
        FeedEntry(post_id=200, link="https://x.com/CommerceDevKit/status/200"),
        FeedEntry(post_id=300, link="https://x.com/CommerceDevKit/status/300"),
    ]

    assert select_new_entries(entries, 150) == (entries[1:], 300)


def test_twitter_feed_resolves_feed_url_template() -> None:
    config = ConfigTwitterFeed(account="CommerceDevKit")

    assert config.resolved_feed_url == "https://nitter.net/CommerceDevKit/rss"
