
from ai_service import ask_gemini

try:
    print("Connecting to Gemini AI...")

    answer = ask_gemini(
        "Explain Python variables in simple English in three sentences."
    )

    print("\nGemini response:")
    print(answer)

    print("\nSUCCESS: Gemini connection is working!")

except Exception as error:
    print("\nGemini connection failed.")
    print("Error:", error)
