import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import uvicorn

from config.settings import settings
from bot.handlers import router
from db.database import init_db
from admin.app import app as admin_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_bot():
    """Telegram botni ishga tushirish."""
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()
    dp.include_router(router)
    
    logger.info("Starting bot...")
    await dp.start_polling(bot)


async def run_admin():
    """Admin panelni ishga tushirish."""
    port = int(os.getenv("PORT", 8000))
    config = uvicorn.Config(
        admin_app, 
        host="0.0.0.0", 
        port=port, 
        log_level="info"
    )
    server = uvicorn.Server(config)
    logger.info(f"Starting admin panel on port {port}...")
    await server.serve()


async def main():
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Run both bot and admin panel concurrently
    await asyncio.gather(
        run_bot(),
        run_admin()
    )


if __name__ == "__main__":
    asyncio.run(main())
