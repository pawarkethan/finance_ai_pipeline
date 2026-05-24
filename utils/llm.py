# ─────────────────────────────────────────────
# utils/llm.py — Gemini LLM helpers
# ─────────────────────────────────────────────

import re
import json
import google.generativeai as genai

from config import GEMINI_API_KEY, MODEL_NAME

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Load Gemini model
_gemini_model = genai.GenerativeModel(MODEL_NAME)


def run_llm(prompt: str) -> str:
    """
    Send a prompt to Gemini and return raw text response.
    """

    response = _gemini_model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.1,
            max_output_tokens=1024,
        ),
    )

    return response.text


def extract_json(text: str) -> dict | None:
    """
    Extract and parse JSON from LLM response.

    Attempts:
    1. ```json fenced block
    2. Largest inline {...}
    3. Outermost braces
    """

    # 1. Extract markdown JSON block
    md = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)

    if md:
        try:
            return json.loads(md.group(1))
        except json.JSONDecodeError:
            pass

    # 2. Extract largest inline JSON object
    matches = sorted(
        re.findall(r"\{[^{}]*\}", text, re.DOTALL),
        key=len,
        reverse=True,
    )

    for m in matches:
        try:
            return json.loads(m)
        except json.JSONDecodeError:
            continue

    # 3. Extract outermost braces
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return None


def llm_json(prompt: str) -> dict:
    """
    Run Gemini and return parsed JSON.
    Returns empty dict on failure.
    """

    return extract_json(run_llm(prompt)) or {}


# ─────────────────────────────────────────────
# TEST BLOCK
# Run this file directly to test Gemini connection
# ─────────────────────────────────────────────

if __name__ == "__main__":

    print("\nTesting Gemini Connection...\n")

    test_prompt = "Say hello in one short sentence."

    try:
        result = run_llm(test_prompt)

        print("Gemini Response:\n")
        print(result)

    except Exception as e:
        print("Error:")
        print(e)