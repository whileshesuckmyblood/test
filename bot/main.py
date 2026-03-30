import asyncio
import os
import logging
import time

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
import aiohttp.web

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TOKEN = os.getenv("BOT_TOKEN")
DOMAIN = os.getenv("DOMAIN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("👋 Бот на webhook работает!")

@dp.message()
async def echo(message: types.Message):
    await message.answer(f"Эхо: {message.text}")

async def healthcheck(request):
    return aiohttp.web.Response(text="Bot is running via webhook!", status=200)

async def on_startup(bot: Bot):
    await asyncio.sleep(2)  # даём серверу время подняться
    if not DOMAIN:
        logging.error("❌ DOMAIN не задан!")
        return
    
    webhook_url = f"https://{DOMAIN}/webhook"
    try:
        await bot.set_webhook(webhook_url, drop_pending_updates=True)
        logging.info(f"✅ Webhook успешно установлен → {webhook_url}")
    except Exception as e:
        logging.error(f"❌ Не удалось установить webhook: {e}")

async def main():
    logging.info("🚀 Запуск Telegram Echo Bot...")
    
    app = aiohttp.web.Application()
    app.router.add_get("/", healthcheck)
    
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
    setup_application(app, dp, bot=bot)

    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

    logging.info(f"✅ Сервер запущен на 0.0.0.0:8080")
    logging.info(f"🌐 Webhook URL: https://{DOMAIN}/webhook")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
