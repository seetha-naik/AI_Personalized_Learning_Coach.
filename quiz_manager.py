import json
from ai_service import ask_gemini


def generate_quiz(subject, topic, level, number_of_questions=5):
    prompt = f"""
Create a multiple-choice quiz.

Subject: {subject}
Topic: {topic}
Level: {level}
Number of questions: {number_of_questions}

Return ONLY valid JSON in this exact format:
{{
  "questions": [
    {{
      "question": "Question text",
      "options": {{
        "A": "First option",
        "B": "Second option",
        "C": "Third option",
        "D": "Fourth option"
      }},
      "answer": "A",
      "explanation": "Simple explanation"
    }}
  ]
}}

Rules:
- Each question must have exactly four options.
- The answer must be A, B, C, or D.
- Keep the language simple.
- Make questions suitable for the selected level.
- Include exactly {number_of_questions} questions.
"""

    response = ask_gemini(prompt)

    # Remove Markdown code fences if the AI includes them.
    cleaned = response.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)

    data = json.loads(cleaned)
    questions = data.get("questions", [])

    if len(questions) != number_of_questions:
        raise ValueError("The AI returned an unexpected number of questions.")

    for question in questions:
        if not all(
            key in question
            for key in ("question", "options", "answer", "explanation")
        ):
            raise ValueError("A quiz question is missing required fields.")

        if set(question["options"]) != {"A", "B", "C", "D"}:
            raise ValueError("Each question must contain options A, B, C, and D.")

        if question["answer"] not in {"A", "B", "C", "D"}:
            raise ValueError("A quiz answer has an invalid option.")

    return questions


def evaluate_quiz(questions, user_answers):
    results = []
    score = 0

    for index, question in enumerate(questions):
        selected = user_answers.get(str(index), "")
        correct = question["answer"]
        is_correct = selected == correct

        if is_correct:
            score += 1

        results.append({
            "question": question["question"],
            "selected": selected,
            "correct": correct,
            "is_correct": is_correct,
            "explanation": question["explanation"]
        })

    return {
        "score": score,
        "total": len(questions),
        "percentage": round(score / len(questions) * 100) if questions else 0,
        "results": results
    }
