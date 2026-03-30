import asyncio
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
import aiohttp.web

TOKEN = os.getenv("BOT_TOKEN")
DOMAIN = os.getenv("DOMAIN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("👋 Бот работает!\nОтправь мне любое сообщение.")


@dp.message()
async def echo(message: types.Message):
    await message.answer(f"Ты написал: {message.text}")


# Healthcheck для главной страницы
async def healthcheck(request: aiohttp.web.Request):
    return aiohttp.web.Response(
        text="✅ Telegram Echo Bot is running successfully!\n\nWebhook: /webhook",
        content_type="text/plain"
    )


async def on_startup(bot: Bot) -> None:
    webhook_url = f"https://{DOMAIN}/webhook"
    await bot.set_webhook(webhook_url)
    print(f"✅ Webhook set to: {webhook_url}")


async def main():
    app = aiohttp.web.Application()

    # Главная страница
    app.router.add_get("/", healthcheck)

    # Webhook для Telegram
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    ).register(app, path="/webhook")

    setup_application(app, dp, bot=bot)

    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, host="0.0.0.0", port=8080)
    await site.start()

    print("🚀 Bot started on port 8080")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
