import asyncio

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from config import TELEGRAM_TOKEN, commands
from loader import dp
import handlers  


async def main():
    bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    await bot.set_my_commands(commands)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())