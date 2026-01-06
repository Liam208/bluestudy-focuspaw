from google import genai
import os
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

apiKey = os.getenv("GEN_AI_KEY")
client = genai.Client(api_key=apiKey)


def ask_gemini(prompt: str, model: str = "gemini-2.5-flash") -> str:
    """
    sends a prompt to the Gemini model and returns the generated response as a string.
    """
    try:
        response = client.models.generate_content_stream(
            model=model,
            contents=prompt,
        )
        result = ""
        for chunk in response:
            result += chunk.text
        return result
    except Exception as e:
        print(f"Error while calling Gemini API: {e}")
        return "Sorry, I couldn't process your request at the moment."
