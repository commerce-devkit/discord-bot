# pyright: reportUnannotatedClassAttribute=false

from contextvars import ContextVar
from functools import cached_property
from typing import TYPE_CHECKING, Annotated, Any, Literal, NamedTuple, override

import discord as dc
from githubkit import GitHub, TokenAuthStrategy
from loguru import logger
from pydantic import (
    AliasChoices,
    BaseModel,
    DirectoryPath,
    Field,
    SecretStr,
    TypeAdapter,
)
from pydantic_settings import (
    BaseSettings,
    CliSuppress,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

if TYPE_CHECKING:
    from pydantic_settings import PydanticBaseSettingsSource

    from toolbox.discord import Account

type WebhookFeedType = Literal["main", "discussions"]
ENV_PREFIX = "BOT__"
DEFAULT_REPO_ALIASES = {
    "main": "website",
    "web": "website",
    "website": "website",
    "meta": ".github",
    "github": ".github",
}


def validate_type[T](obj: object, typ: type[T]) -> T:
    adapter = TypeAdapter(typ, config={"arbitrary_types_allowed": True})
    return adapter.validate_python(obj, strict=True)


def _alias(name: str) -> AliasChoices:
    return AliasChoices(name, ENV_PREFIX + name.upper())


def _default_repo_aliases() -> dict[str, str]:
    return DEFAULT_REPO_ALIASES.copy()


class ConfigRoles(BaseModel):
    mod: int
    helper: int


class ConfigTokens(BaseModel):
    discord: SecretStr
    github: SecretStr


class ConfigBrand(BaseModel):
    bot_name: str = "DevKit Bot"
    community_name: str = "Commerce DevKit"
    moderator_name: str = "DevKit Moderator"


class ConfigGitHub(BaseModel):
    owner: str = "commerce-devkit"
    default_repo: str = "website"
    repo_aliases: dict[str, str] = Field(default_factory=_default_repo_aliases)
    ignored_issue_comment_logins: list[str] = Field(default_factory=list)


class ConfigDocs(BaseModel):
    base_url: str
    source_owner: str
    source_repo: str
    nav_path: str = "docs/nav.json"
    nav_sections: dict[str, str] = Field(default_factory=dict)
    page_sources: dict[str, str] = Field(default_factory=dict)
    url_paths: dict[str, str] = Field(default_factory=dict)


class ConfigChannels(BaseModel):
    help: int
    log: int
    media: int
    showcase: int
    serious: list[int] = Field(default_factory=list)
    help_tags: dict[str, int] = Field(default_factory=dict)


class Channels(NamedTuple):
    help: dc.ForumChannel
    log: dc.TextChannel


class WebhookChannels(BaseModel):
    main: int
    discussions: int


class ConfigWebhook(BaseModel):
    _bot: dc.Client
    url: SecretStr
    secret: SecretStr | None = None
    channel_ids: Annotated[WebhookChannels, Field(alias="channels")]

    @cached_property
    def channels(self) -> dict[WebhookFeedType, dc.TextChannel]:
        assert self._bot
        channels = {
            "main": self._bot.get_channel(self.channel_ids.main),
            "discussions": self._bot.get_channel(self.channel_ids.discussions),
        }
        return validate_type(channels, dict[WebhookFeedType, dc.TextChannel])


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        cli_prog_name="uv run -m app",
        cli_avoid_json=True,
        cli_hide_none_type=True,
        cli_parse_args=True,
        cli_kebab_case=True,
        cli_use_class_docs_for_groups=True,
        env_prefix=ENV_PREFIX,
        env_nested_delimiter="__",
        toml_file="config.toml",
    )

    bot: CliSuppress[dc.Client]
    guild_id: int | None = None
    data_dir: DirectoryPath
    sentry_dsn: SecretStr | None = None

    brand: ConfigBrand = Field(default_factory=ConfigBrand)
    docs: ConfigDocs | None = None
    github: ConfigGitHub = Field(default_factory=ConfigGitHub)
    tokens: ConfigTokens
    role_ids: Annotated[ConfigRoles, Field(validation_alias=_alias("roles"))]
    channel_ids: Annotated[ConfigChannels, Field(validation_alias=_alias("channels"))]
    webhook: ConfigWebhook

    @override
    def model_post_init(self, context: Any, /) -> None:
        self.webhook._bot = self.bot  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

    @classmethod
    @override
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            env_settings,
            init_settings,
            TomlConfigSettingsSource(settings_cls),
            dotenv_settings,
        )

    @cached_property
    def channels(self) -> Channels:
        logger.debug("fetching channels: help, log")
        channels = (
            self.bot.get_channel(self.channel_ids.help),
            self.bot.get_channel(self.channel_ids.log),
        )
        return validate_type(channels, Channels)

    @cached_property
    def guild(self) -> dc.Guild:
        logger.debug("fetching configured guild")
        if (id_ := self.guild_id) and (guild := self.bot.get_guild(id_)):
            logger.trace("found configured guild")
            return guild
        guild = self.bot.guilds[0]
        logger.info(
            "BOT_GUILD_ID unset or specified guild not found; using bot's first guild: "
            "{name} (ID: {id})",
            name=guild.name,
            id=guild.id,
        )
        return guild

    def is_privileged(self, member: dc.Member) -> bool:
        return not (
            member.get_role(self.role_ids.mod) is None
            and member.get_role(self.role_ids.helper) is None
        )

    def is_mod(self, user: Account) -> bool:
        member = self.guild.get_member(user.id)
        return member is not None and member.get_role(self.role_ids.mod) is not None


config_var = ContextVar[Config]("config")
config = config_var.get
gh_var = ContextVar[GitHub[TokenAuthStrategy]]("gh")
gh = gh_var.get
