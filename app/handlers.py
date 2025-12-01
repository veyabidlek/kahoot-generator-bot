import json
from io import BytesIO

from aiogram import types
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from loader import dp, user_data
from states import QuestionGeneration
from callback_data import (
    QuestionsContextCD,
    QuestionsCountCD,
    QuestionsDifficultyLevelCD,
)
from keyboards import (
    generate_questions_context_keyboard,
    generate_questions_count_keyboard,
    generate_questions_difficulty_keyboard,
)
from deepseek import get_deepseek_response
from utils import (
    extract_content_from_message,
    quiz_to_dataframe,
    dataframe_to_excel_bytes,
    clean_and_parse_json,
)


from aiogram.enums import ParseMode

from aiogram.enums import ParseMode

@dp.message(Command("start"))
async def command_start_handler(message: Message):
    text = """
<b>Welcome to the Kahoot Generator Bot! 😊</b>

Here’s what you can do:
• Use <code>/help</code> to learn how the bot works.
• Use <code>/generate</code> to create a new Kahoot quiz.

Just upload a file or send a text prompt — I’ll do the rest!
"""
    await message.answer(text)


@dp.message(Command("generate"))
async def command_generate_handler(message: Message, state: FSMContext):
    text = """
Give me a file or send a message
(but messages support only up to 4096 characters ‼️)
"""
    await message.answer(text)
    await state.set_state(QuestionGeneration.waiting_for_content)


@dp.message(Command("help"))
async def command_help_handler(message: Message):
    text = """
<b>How does this bot work</b> ❓

This bot creates <b>Kahoot-style quizzes</b> based on the text you provide.

Just upload a PDF or send a text message — the bot will analyze the content and generate a set of high-quality quiz questions for you.

⚠️ <b>Important:</b>
The bot can extract <b>only real text</b> from PDFs.
If your PDF is a <b>scanned document</b> or contains text <b>inside images</b>, that text cannot be read.

After sending your content, the bot will guide you through choosing:
• How many questions to generate
• The difficulty level
• Whether to use only your content or also general knowledge

You will then receive a ready-to-import <b>Excel (.xlsx)</b> file.


📥 <b>How to import the quiz into Kahoot</b>

1. Open Kahoot and click <b>Create</b> in the top-right corner.
2. In the left panel, click <b>Add question</b>.
3. Choose <b>Import</b>.
4. Select <b>Import spreadsheet</b> and upload the Excel file from this bot.

Your Kahoot will be generated automatically!
"""
    await message.answer(text)

@dp.message(QuestionGeneration.waiting_for_content)
async def receive_content(message: Message, state: FSMContext):
    user_id = message.from_user.id

    content = await extract_content_from_message(message)
    if not content:
        await message.answer("Send text or document")
        return

    user_data.setdefault(user_id, {})
    user_data[user_id]["content"] = content

    await state.clear()
    await generate_questions_context_handler(message)


# Step 2: ask to include any other context
async def generate_questions_context_handler(message: Message):
    await message.answer(
        "Choose the context of Kahoot:",
        reply_markup=generate_questions_context_keyboard(),
    )


# Step 3: how many questions
async def generate_number_of_questions_handler(message: Message):
    await message.answer(
        "Choose the number of questions:",
        reply_markup=generate_questions_count_keyboard(),
    )


# Step 4: Ask difficulty
async def generate_difficulty_of_questions_handler(message: Message):
    await message.answer(
        "Choose the difficulty of Kahoot:",
        reply_markup=generate_questions_difficulty_keyboard(),
    )


@dp.callback_query(QuestionsContextCD.filter())
async def get_questions_context(
    callback: types.CallbackQuery, callback_data: QuestionsContextCD
):
    user_id = callback.from_user.id
    user_data.setdefault(user_id, {})
    user_data[user_id]["is_context_limited_to_data"] = (
        callback_data.is_context_limited_to_data
    )

    await callback.answer()
    await generate_number_of_questions_handler(callback.message)


@dp.callback_query(QuestionsCountCD.filter())
async def get_questions_number(
    callback: types.CallbackQuery, callback_data: QuestionsCountCD
):
    user_id = callback.from_user.id
    user_data.setdefault(user_id, {})
    user_data[user_id]["count"] = callback_data.count

    await callback.answer()
    await generate_difficulty_of_questions_handler(callback.message)


@dp.callback_query(QuestionsDifficultyLevelCD.filter())
async def get_questions_difficulty(
    callback: types.CallbackQuery, callback_data: QuestionsDifficultyLevelCD
):
    user_id = callback.from_user.id
    user_data.setdefault(user_id, {})
    user_data[user_id]["difficulty"] = callback_data.difficulty.value

    await callback.answer("Processing...")
    await callback.message.answer("Wait. Your Kahoot is being created... ⏳")

    try:
        res_str = await get_deepseek_response(user_data[user_id])
        
        # Use the robust JSON parser
        res_json = clean_and_parse_json(res_str)
        
        # Validate we got questions
        if not res_json:
            await callback.message.answer(
                "❌ AI returned empty questions list. Please try again."
            )
            return
        
        # Validate question structure
        for idx, q in enumerate(res_json):
            if not isinstance(q, dict):
                await callback.message.answer(
                    f"❌ Question {idx + 1} has invalid format. Please try again."
                )
                return
            
            required_fields = ["question", "answers", "correct", "time_limit"]
            missing = [f for f in required_fields if f not in q]
            if missing:
                await callback.message.answer(
                    f"❌ Question {idx + 1} is missing fields: {', '.join(missing)}. Please try again."
                )
                return
        
        df = quiz_to_dataframe(res_json)
        excel_file: BytesIO = dataframe_to_excel_bytes(df)

        await callback.message.answer_document(
            BufferedInputFile(excel_file.getvalue(), filename="KahootQuiz.xlsx")
        )
        
    except ValueError as e:
        await callback.message.answer(
            f"❌ Failed to parse quiz questions: {e}\n\n"
            "This usually happens when the AI response is malformed. Please try again."
        )
    except Exception as e:
        await callback.message.answer(
            f"❌ An unexpected error occurred: {type(e).__name__}: {e}\n\n"
            "Please try again or contact support if the issue persists."
        )