from io import BytesIO
from typing import Any, Dict, List, Optional

import pandas as pd
from PyPDF2 import PdfReader
from aiogram.types import Message


async def extract_content_from_message(message: Message) -> Optional[str]:
    if message.text:
        return message.text

    if message.document:
        file = await message.bot.get_file(message.document.file_id)
        file_bytes = BytesIO()
        await message.bot.download_file(file.file_path, file_bytes)
        file_bytes.seek(0)

        if message.document.file_name.lower().endswith(".pdf"):
            reader = PdfReader(file_bytes)
            content = ""
            for page in reader.pages:
                page_text = page.extract_text() or ""
                content += page_text + "\n"
            return content.strip()

        return file_bytes.read().decode("utf-8", errors="ignore")

    return None



def quiz_to_dataframe(questions: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for q in questions:
        row = [
            str(q.get("question", ""))[:120],
            str(q.get("answers", ["", "", "", ""])[0])[:75],
            str(q.get("answers", ["", "", "", ""])[1])[:75],
            str(q.get("answers", ["", "", "", ""])[2])[:75],
            str(q.get("answers", ["", "", "", ""])[3])[:75],
            q.get("time_limit", 60),
            q.get("correct", ""),
        ]
        rows.append(row)

    columns = [
        "Question - max 120 characters",
        "Answer 1 - max 75 characters",
        "Answer 2 - max 75 characters",
        "Answer 3 - max 75 characters",
        "Answer 4 - max 75 characters",
        "Time limit (sec)",
        "Correct answer(s)",
    ]
    return pd.DataFrame(rows, columns=columns)


def dataframe_to_excel_bytes(df: pd.DataFrame, filename: str = "KahootQuiz.xlsx") -> BytesIO:
    excel_file = BytesIO()
    df.to_excel(excel_file, index=False, engine="openpyxl")
    excel_file.seek(0)
    return excel_file