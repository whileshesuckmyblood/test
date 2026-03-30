import asyncio
import os
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
import aiohttp.web

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TOKEN = os.getenv("BOT_TOKEN")
DOMAIN = os.getenv("DOMAIN")
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("👋 Бот работает через webhook!")

@dp.message()
async def echo(message: types.Message):
    await message.answer(f"я не лох) {message.text}")

# healthcheck (для nginx / мониторинга)
async def healthcheck(request):
    return aiohttp.web.Response(text="OK", status=200)

# ВАЖНО: нормальная установка webhook
async def on_startup(bot: Bot):
    await asyncio.sleep(5)  # даём nginx и сети подняться

    if not DOMAIN:
        logging.error("❌ DOMAIN не указан")
        return

    webhook_url = f"https://{DOMAIN}/webhook"

    try:
        result = await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )
        if result:
            logging.info(f"✅ Webhook установлен: {webhook_url}")
        else:
            logging.error("❌ set_webhook вернул False")
    except Exception as e:
        logging.exception("❌ Ошибка при установке webhook")

async def main():
    logging.info("🚀 Запуск бота...")

    # 👇 ВОТ ЭТО КРИТИЧЕСКИ ВАЖНО
    dp.startup.register(on_startup)

    app = aiohttp.web.Application()

    # health endpoint
    app.router.add_get("/", healthcheck)

    # webhook endpoint
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    ).register(app, path="/webhook")

    setup_application(app, dp, bot=bot)

    runner = aiohttp.web.AppRunner(app)
    await runner.setup()

    site = aiohttp.web.TCPSite(
        runner,
        host="0.0.0.0",
        port=PORT
    )
    await site.start()

    logging.info(f"✅ Сервер слушает порт {PORT}")
    logging.info(f"🌐 Webhook URL: https://{DOMAIN}/webhook")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
