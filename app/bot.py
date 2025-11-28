import asyncio
import logging
import sys
import os
import json 
import re
from PyPDF2 import PdfReader
from io import BytesIO
from dotenv import load_dotenv

import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BufferedInputFile
from enum import Enum

from deepseek import get_deepseek_response

class QuestionGeneration(StatesGroup):
    waiting_for_content = State()

class QuestionsDifficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class QuestionsMode(Enum):
  LEARN = "LEARN"
  EXAM = "EXAM"

class QuestionsCountCD(CallbackData, prefix="qcount"):
    count: int

class QuestionsDifficultyLevelCD(CallbackData, prefix="qdifficulty"):
    difficulty: QuestionsDifficulty
    
class QuestionsModeCD(CallbackData, prefix="qmode"):
  mode: QuestionsMode
  
class QuestionsContextCD(CallbackData, prefix="qcontext"):
  is_context_limited_to_data: bool



load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

commands = [
    types.BotCommand(command="start", description="Ботты бастау")
    #types.BotCommand(command="help", description="Бұл бот не істейді?"),
]

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

user_data = {}

@dp.message(QuestionGeneration.waiting_for_content)
async def receive_content(message: Message, state: FSMContext):
    user_id = message.from_user.id
    content = ""
    if message.text:    
        content = message.text
    elif message.document:
        file = await message.bot.get_file(message.document.file_id)
        file_bytes = BytesIO()
        await message.bot.download_file(file.file_path, file_bytes)
        file_bytes.seek(0)
        
        if message.document.file_name.endswith(".pdf"):
            reader = PdfReader(file_bytes)
            for page in reader.pages:
                content += page.extract_text() + "\n"
        else:
            content = file_bytes.read().decode("utf-8", errors="ignore")
    else: 
        await message.answer("Send text or document")
        return
    
    user_data.setdefault(user_id, {})
    user_data[user_id]["content"] = content
    
    await state.clear()
    
    await generate_questions_context_handler(message)



# Step 1: ask mode 
async def generate_questions_mode_handler(message: Message):
  keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Learn", callback_data=QuestionsModeCD(mode=QuestionsMode.LEARN).pack())],
        [InlineKeyboardButton(text="Test", callback_data=QuestionsModeCD(mode=QuestionsMode.EXAM).pack())],
    ]
  )
  await message.answer("Choose the mode of Kahoot: ", reply_markup=keyboard)

# Step 2: ask to include any other context
async def generate_questions_context_handler(message: Message):
  keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
      [InlineKeyboardButton(text="Kahoot questions are based only on provided data", callback_data=QuestionsContextCD(is_context_limited_to_data=True).pack())],
      [InlineKeyboardButton(text="Kahoot questions can use external knowledge", callback_data=QuestionsContextCD(is_context_limited_to_data=False).pack())]
    ]
  )
  await message.answer("Choose the context of Kahoot:", reply_markup=keyboard)
  
# Step 3: how many questions
async def generate_number_of_questions_handler(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="10", callback_data=QuestionsCountCD(count=10).pack())],
            [InlineKeyboardButton(text="20", callback_data=QuestionsCountCD(count=20).pack())],
            [InlineKeyboardButton(text="30", callback_data=QuestionsCountCD(count=30).pack())],
            [InlineKeyboardButton(text="40", callback_data=QuestionsCountCD(count=40).pack())],
            [InlineKeyboardButton(text="50", callback_data=QuestionsCountCD(count=50).pack())],
        ]
    )
    await message.answer("Choose the number of questions:", reply_markup=keyboard)


# Step 4: Ask difficulty
async def generate_difficulty_of_questions_handler(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Easy", callback_data=QuestionsDifficultyLevelCD(difficulty=QuestionsDifficulty.EASY).pack())],
            [InlineKeyboardButton(text="Medium", callback_data=QuestionsDifficultyLevelCD(difficulty=QuestionsDifficulty.MEDIUM).pack())],
            [InlineKeyboardButton(text="Difficult", callback_data=QuestionsDifficultyLevelCD(difficulty=QuestionsDifficulty.HARD).pack())],
        ]
    )
    await message.answer("Choose the difficulty of Kahoot:", reply_markup=keyboard)


@dp.callback_query(QuestionsModeCD.filter())
async def get_questions_mode(callback: types.CallbackQuery, callback_data: QuestionsModeCD):
    user_id = callback.from_user.id
    user_data[user_id]["mode"] = callback_data.mode.value
    await callback.answer()
    await generate_questions_context_handler(callback.message)
    
@dp.callback_query(QuestionsContextCD.filter())
async def get_questions_context(callback: types.CallbackQuery, callback_data: QuestionsContextCD):
    user_id = callback.from_user.id
    user_data[user_id]["is_context_limited_to_data"] = callback_data.is_context_limited_to_data
    await callback.answer()
    await generate_number_of_questions_handler(callback.message)
    
@dp.callback_query(QuestionsCountCD.filter())
async def get_questions_number(callback: types.CallbackQuery, callback_data: QuestionsCountCD):
    user_id = callback.from_user.id
    user_data[user_id]["count"] = callback_data.count
    await callback.answer()
    await generate_difficulty_of_questions_handler(callback.message)  

MAX_MESSAGE_LENGTH = 4000
def chunk_message(text: str):
    for i in range(0, len(text), MAX_MESSAGE_LENGTH):
        yield text[i:i + MAX_MESSAGE_LENGTH]
        
@dp.callback_query(QuestionsDifficultyLevelCD.filter())
async def get_questions_difficulty(callback: types.CallbackQuery, callback_data: QuestionsDifficultyLevelCD):
    user_id = callback.from_user.id
    user_data[user_id]["difficulty"] = callback_data.difficulty.value
    await callback.answer("Processing...")
    await callback.message.answer("Wait. Your Kahoot is being created... ⏳")
    res_str = await get_deepseek_response(user_data[user_id])
    match = re.search(r"\[.*\]", res_str, re.DOTALL)
    if not match:
        await callback.message.answer("❌ Failed to parse quiz questions. No JSON found in response.")
        return

    res_json = match.group(0)
    try:
        res = json.loads(res_json)
    except json.JSONDecodeError:
        await callback.message.answer("❌ Failed to parse quiz questions. JSON is invalid.")
        return
    data = []
    for q in res:
        row = [
            q["question"][:120],  
            q["answers"][0][:75],
            q["answers"][1][:75],
            q["answers"][2][:75],
            q["answers"][3][:75],
            q.get("time_limit", 60),
            q["correct"]
        ]
        data.append(row)
    columns = [
        "Question - max 120 characters",
        "Answer 1 - max 75 characters",
        "Answer 2 - max 75 characters",
        "Answer 3 - max 75 characters",
        "Answer 4 - max 75 characters",
        "Time limit (sec)",
        "Correct answer(s)"
    ]
    
    df = pd.DataFrame(data, columns=columns)
    excel_file = BytesIO()
    df.to_excel(excel_file, index=False, engine='openpyxl')
    excel_file.seek(0)

    await callback.message.answer_document(
        BufferedInputFile(excel_file.getvalue(), filename="KahootQuiz.xlsx")
    )





@dp.message(Command("start"))
async def command_start_handler(message: Message, state: FSMContext):
    await message.answer("Give me a file or send a message (but message supports only up to 4096 characters ‼️)")
    await state.set_state(QuestionGeneration.waiting_for_content)


async def main():
    bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties())
    await bot.set_my_commands(commands)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        stream=sys.stdout,
    )
    asyncio.run(main())
