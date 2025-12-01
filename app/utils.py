import json
import re
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


def clean_and_parse_json(raw_response: str) -> List[Dict[str, Any]]:
    """
    Clean and parse JSON response from AI, handling common issues:
    - Markdown code blocks (```json ... ```)
    - Trailing commas
    - Wrapped objects instead of arrays
    - Extra whitespace and newlines
    """
    # Remove markdown code blocks
    cleaned = re.sub(r'^```(?:json)?\s*', '', raw_response.strip())
    cleaned = re.sub(r'```\s*$', '', cleaned)
    
    # Remove any leading/trailing whitespace
    cleaned = cleaned.strip()
    
    # Try to parse as-is first
    try:
        parsed = json.loads(cleaned)
        
        # If it's wrapped in an object with a "questions" key, unwrap it
        if isinstance(parsed, dict):
            if "questions" in parsed:
                parsed = parsed["questions"]
            elif "data" in parsed:
                parsed = parsed["data"]
            elif "quiz" in parsed:
                parsed = parsed["quiz"]
            # If it's an object with numeric keys, convert to list
            elif all(k.isdigit() for k in parsed.keys()):
                parsed = [parsed[k] for k in sorted(parsed.keys(), key=int)]
            else:
                # Try to find the first list value
                for value in parsed.values():
                    if isinstance(value, list):
                        parsed = value
                        break
        
        if not isinstance(parsed, list):
            raise ValueError(f"Expected a list, got {type(parsed).__name__}")
        
        return parsed
    
    except json.JSONDecodeError as e:
        # Try to fix common issues
        
        # Remove trailing commas before closing brackets/braces
        cleaned = re.sub(r',\s*([\]}])', r'\1', cleaned)
        
        # Try to extract JSON array if it's embedded in text
        array_match = re.search(r'\[\s*\{.*\}\s*\]', cleaned, re.DOTALL)
        if array_match:
            cleaned = array_match.group(0)
        
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                # Apply same unwrapping logic
                for key in ["questions", "data", "quiz"]:
                    if key in parsed and isinstance(parsed[key], list):
                        return parsed[key]
            if isinstance(parsed, list):
                return parsed
            raise ValueError(f"Could not extract array from response")
        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse JSON even after cleaning. Original error: {e}")


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