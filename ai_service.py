import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

# Try alternative text-generation models if one is unavailable.
MODELS = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
]


def get_client():
    if not API_KEY:
        raise ValueError(
            "Gemini API key is missing. Check your .env file."
        )

    return genai.Client(
        api_key=API_KEY,
        http_options={"timeout": 30000}
    )


def ask_gemini(prompt):
    if not prompt or not prompt.strip():
        raise ValueError("Please provide a prompt.")

    client = get_client()
    errors = []

    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )

            if response.text and response.text.strip():
                return response.text

            errors.append(f"{model}: Empty response")

        except Exception as error:
            errors.append(f"{model}: {error}")
            print(f"Model {model} failed. Trying the next model...")

        time.sleep(1)

    raise RuntimeError(
        "All Gemini models failed. Please try again later.\n"
        + "\n".join(errors)
    )
