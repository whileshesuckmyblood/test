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
    await message.answer("Бот работает")


@dp.message()
async def echo(message: types.Message):
    await message.answer(message.text)


async def on_startup(bot: Bot) -> None:
    await bot.set_webhook(f"https://{DOMAIN}/webhook")

async def main():
    app = aiohttp.web.Application()

    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    ).register(app, path="/webhook")

    setup_application(app, dp, bot=bot)

    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, host="0.0.0.0", port=8080)
    await site.start()

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
