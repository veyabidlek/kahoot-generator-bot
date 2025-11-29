from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from callback_data import (
    QuestionsCountCD,
    QuestionsDifficultyLevelCD,
    QuestionsContextCD,
)
from states import QuestionsDifficulty


def generate_questions_context_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔒 Use ONLY the provided text (no outside info)",
                    callback_data=QuestionsContextCD(
                        is_context_limited_to_data=True
                    ).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🌐 Allow general knowledge (still based on your topic)",
                    callback_data=QuestionsContextCD(
                        is_context_limited_to_data=False
                    ).pack(),
                )
            ],
        ]
    )


def generate_questions_count_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="10 questions",
                    callback_data=QuestionsCountCD(count=10).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text="20 questions",
                    callback_data=QuestionsCountCD(count=20).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text="30 questions",
                    callback_data=QuestionsCountCD(count=30).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text="40 questions",
                    callback_data=QuestionsCountCD(count=40).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text="50 questions",
                    callback_data=QuestionsCountCD(count=50).pack()
                )
            ],
        ]
    )


def generate_questions_difficulty_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🟢 Easy — basic recall & simple reasoning",
                    callback_data=QuestionsDifficultyLevelCD(
                        difficulty=QuestionsDifficulty.EASY
                    ).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🟡 Medium — moderate reasoning, 1–2 steps",
                    callback_data=QuestionsDifficultyLevelCD(
                        difficulty=QuestionsDifficulty.MEDIUM
                    ).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔴 Hard — multi-step reasoning, deeper concepts",
                    callback_data=QuestionsDifficultyLevelCD(
                        difficulty=QuestionsDifficulty.HARD
                    ).pack(),
                )
            ],
        ]
    )