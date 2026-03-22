import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config.settings import settings
from bot.handlers import router
from db.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Initialize bot
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()
    dp.include_router(router)
    
    logger.info("Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
