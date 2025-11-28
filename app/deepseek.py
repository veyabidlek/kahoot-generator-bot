import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

async def get_deepseek_response(config: dict):
    prompt = f"""
You are a quiz generator. Generate exactly {config['count']} quiz questions in JSON format. 
Each question should have:
- "question": the question text related to "{config['content']}"
- "answers": a list of 4 plausible answer options
- "correct": the index (1-4) of the correct answer
- "time_limit": an integer in seconds (default 60)

Constraints:
- Difficulty: {config['difficulty']}
- Context limited to data: {config['is_context_limited_to_data']}
  - If True, only use the data provided in "{config['content']}"
  - If False, you may also use general knowledge but still stay relevant

Output format:
[
    {{
        "question": "...",
        "answers": ["...", "...", "...", "..."],
        "correct": "...",
        "time_limit": 60
    }},
    ...
]
Do not include any explanations or extra text—only return valid JSON.
"""
    response = await client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": prompt},
        ],
    )
    return response.choices[0].message.content
