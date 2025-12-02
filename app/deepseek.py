import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
USE_DEEPSEEK = os.getenv("USE_DEEPSEEK", "false").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Initialize the appropriate client based on USE_DEEPSEEK
if USE_DEEPSEEK:
    client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    MODEL_NAME = "deepseek-chat"
else:
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    MODEL_NAME = "gpt-5-mini"

async def get_deepseek_response(config: dict):
    if config.get("is_context_limited_to_data"):
        context_rule = (
            "You MUST base every question and answer ONLY on the context below. "
            "Do not use any outside knowledge beyond simple arithmetic or logic "
            "that can be directly inferred from the context."
        )
    else:
        context_rule = (
            "You MAY also use relevant general knowledge, but every question "
            "must still be clearly related to the topic and ideas in the context below."
        )

    system_prompt = """
You are an expert educational assessment designer.
Your job is to create high-quality multiple-choice questions that test
UNDERSTANDING and REASONING, not just memorization.

General principles:
- Focus on conceptual understanding, reasoning, and multi-step thinking.
- Use realistic, plausible distractors (wrong answers) that reflect common mistakes.
- Ensure exactly ONE correct answer per question.
- Do NOT use options like "All of the above" or "None of the above".
- Use clear, concise language appropriate for students.
"""

    user_prompt = f"""
Create EXACTLY {config['count']} multiple-choice quiz questions.

Context (source material):
\"\"\" 
{config['content']}
\"\"\"

{context_rule}

Difficulty level: {config['difficulty']}.

Interpretation of difficulty:
- easy: mostly single-step questions; basic understanding of definitions, simple calculations.
- medium: 1–2 steps of reasoning; combine ideas from the context; may require interpreting notation or simple algebra/logic.
- hard: multi-step reasoning; combine several ideas; may involve identifying errors, edge cases, or subtle properties.

Question design requirements:
- Every question must be meaningfully connected to the context and its topic.
- Include a mix of:
  - conceptual understanding (what, why, properties),
  - application (use a concept to solve a new instance),
  - reasoning / multi-step calculation (especially for medium/hard).
- Avoid trivial copy-paste questions where the answer is literally a phrase from the context with no reasoning.

Output format (IMPORTANT):
- Output MUST be a JSON object with a "questions" key containing an array.
- Each element of the array is an object with the fields:
  - "question": string, the question text.
  - "answers": array of exactly 4 strings, the answer options.
  - "correct": integer random(1 to 4) with equal probability distribution, no bias, the index of the correct option in "answers".
  - "time_limit": integer (seconds), usually between 30 and 90, depending on complexity.

Example of the required structure (schema, not actual content):
{{
  "questions": [
    {{
      "question": "…",
      "answers": ["…", "…", "…", "…"],
      "correct": 2,
      "time_limit": 60
    }},
    ...
  ]
}}

Additional rules:
- Randomize the position of the correct answer among the 4 options.
- Do NOT include any explanations, reasoning steps, comments, or extra text.
- The JSON must be syntactically valid (no trailing commas, proper escaping of quotes).
- Ensure all strings are properly escaped and quoted.
"""

    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={
            'type': 'json_object'
        }
    )

    return response.choices[0].message.content