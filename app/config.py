import os
from dotenv import load_dotenv
from aiogram import types

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

commands = [
    types.BotCommand(command="start", description="Start bot 🚀"),
    types.BotCommand(command="generate", description="Generate Kahoot 📄"),
    types.BotCommand(command="help", description="What does this bot do❓"),
]