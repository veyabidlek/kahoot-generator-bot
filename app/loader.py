import logging
import sys

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    stream=sys.stdout,
)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Simple in-memory user storage
user_data: dict[int, dict] = {}