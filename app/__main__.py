import asyncio
from contextlib import suppress

from loguru import logger

from app.bot import DevkitBot
from app.config import config


async def main() -> None:
    async with DevkitBot() as bot:
        logger.debug("starting the bot")
        await bot.start(config().tokens.discord.get_secret_value())


with suppress(KeyboardInterrupt):
    asyncio.run(main())
