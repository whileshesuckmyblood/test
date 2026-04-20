import asyncio
import os
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
import aiohttp.web
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TOKEN = os.getenv("BOT_TOKEN")
DOMAIN = os.getenv("DOMAIN")
PORT = int(os.getenv("PORT", 8080))
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

redis = Redis.from_url(REDIS_URL, decode_responses=True)
storage = RedisStorage(redis=redis)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=storage)

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("бот работает")

@dp.message()
async def echo(message: types.Message):
    user_id = message.from_user.id
    previous_text = await redis.get(f"last_msg:{user_id}")

    await redis.set(f"last_msg:{user_id}", message.text, ex=60)

    reply = f"wow: {message.text}"
    if previous_text:
        reply += f"\n{previous_text}"
    await message.answer(reply)

async def healthcheck(request):
    return aiohttp.web.Response(text="OK", status=200)

async def on_startup(bot: Bot):
    await asyncio.sleep(5)

    if not DOMAIN:
        logging.error("домен не указан")
        return

    webhook_url = f"https://{DOMAIN}/webhook"

    try:
        result = await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )
        if result:
            logging.info(f"вебхук встал: {webhook_url}")
        else:
            logging.error("вебхук вернул False")
    except Exception as e:
        logging.exception("ошибка при установки вебхука")

async def main():
    logging.info("запускается)")

    dp.startup.register(on_startup)

    app = aiohttp.web.Application()

    app.router.add_get("/", healthcheck)

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

    logging.info(f"сервер работает на порту {PORT}")
    logging.info(f"вебхук: https://{DOMAIN}/webhook")
    try:
        await asyncio.Event().wait()
    finally:
        await redis.close()

if __name__ == "__main__":
    asyncio.run(main())
