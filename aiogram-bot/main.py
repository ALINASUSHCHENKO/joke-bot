import asyncio
import os
import sys
from dotenv import load_dotenv

if not load_dotenv():
    print("Ошибка: Файл .env не найден!")
    sys.exit(1)

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from database.models import db_manager
from handlers import user_handlers, ai_handlers

async def main():
    await db_manager.init_db()
    
    proxy_ip = "91.216.186.121"
    proxy_port = "8000"
    proxy_user = "zNYzxM"
    proxy_pass = "TEqKBm"

    proxy_url = f"socks5://{proxy_user}:{proxy_pass}@{proxy_ip}:{proxy_port}"
    
    print("Подключаемся через индивидуальный SOCKS5 прокси...")
    session = AiohttpSession(proxy=proxy_url)
    
    bot = Bot(token=os.getenv("BOT_TOKEN"), session=session)
    dp = Dispatcher()
    
    dp.include_router(user_handlers.router)
    dp.include_router(ai_handlers.router)
    
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")
