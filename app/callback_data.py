from aiogram.filters.callback_data import CallbackData
from states import QuestionsDifficulty


class QuestionsCountCD(CallbackData, prefix="qcount"):
    count: int


class QuestionsDifficultyLevelCD(CallbackData, prefix="qdifficulty"):
    difficulty: QuestionsDifficulty


class QuestionsContextCD(CallbackData, prefix="qcontext"):
    is_context_limited_to_data: bool