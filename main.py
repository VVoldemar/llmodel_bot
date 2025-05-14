import os
import asyncio
import aiogram
import dotenv
import logging

import routers
import middleware
import settings

from models import db_session

dotenv.load_dotenv()

bot = aiogram.Bot(token=os.getenv("BOT_TOKEN"))
dp = aiogram.Dispatcher()
dp.update.outer_middleware(middleware.db.DbSessionMiddleware())

async def main():
    db_session.global_init(settings.DB_FILE)
    dp.include_routers(*routers.routers)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('exit')