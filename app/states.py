from aiogram.fsm.state import State, StatesGroup
from enum import Enum


class QuestionGeneration(StatesGroup):
    waiting_for_content = State()


class QuestionsDifficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"