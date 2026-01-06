import os
import random
import json
import re
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Filter out empty strings to prevent "Missing key" errors
raw_keys = os.getenv("GEN_AI_KEY_FLASH", "").split(",")
FLASHCARD_KEYS = [k.strip() for k in raw_keys if k.strip()]


def clean_ai_json(text):
    """
    Extracts JSON from the AI response, even if it includes markdown or extra text.
    """
    # Find anything between [ ] or { }
    match = re.search(r"(\[.*\]|\{.*\})", text, re.DOTALL)
    if match:
        return match.group(1)
    return text


def generate_flashcards_ai(prompt: str, model: str = "gemini-2.5-flash") -> list:
    if not FLASHCARD_KEYS:
        print("CRITICAL: No flashcard keys found in .env!")
        return []

    # Shuffle to pick a random starting key
    available_keys = FLASHCARD_KEYS.copy()
    random.shuffle(available_keys)

    for api_key in available_keys:
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )

            # Clean and parse the response
            cleaned_text = clean_ai_json(response.text)
            return json.loads(cleaned_text)

        except Exception as e:
            # If it's a rate limit (429) or other API error, try next key
            print(f"Key failed or rate limited. Trying next... Error: {e}")
            continue

    return []  # Return empty list if all keys fail
