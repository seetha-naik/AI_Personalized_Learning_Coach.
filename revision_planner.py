from collections import defaultdict
from ai_service import ask_gemini


def find_weak_topics(quiz_results, threshold=60):
    topic_scores = defaultdict(list)

    for result in quiz_results:
        topic = result.get("topic")
        percentage = result.get("percentage")

        if topic and percentage is not None:
            topic_scores[topic].append(float(percentage))

    summary = []

    for topic, scores in topic_scores.items():
        average = round(sum(scores) / len(scores), 1)
        summary.append({
            "topic": topic,
            "average_score": average,
            "attempts": len(scores),
            "needs_revision": average < threshold
        })

    return sorted(
        summary,
        key=lambda item: item["average_score"]
    )


def create_revision_plan(subject, quiz_results, daily_minutes=30):
    if not quiz_results:
        return (
            "Complete at least one quiz first. "
            "Your results will help create a personalized revision plan."
        )

    topics = find_weak_topics(quiz_results)
    weak_topics = [
        item for item in topics if item["needs_revision"]
    ]

    if not weak_topics:
        weak_topics = topics[:3]

    topic_details = "\n".join(
        f"- {item['topic']}: average score "
        f"{item['average_score']}% across "
        f"{item['attempts']} quiz attempt(s)"
        for item in weak_topics
    )

    prompt = f"""
You are a friendly AI learning coach.

Create a personalized revision plan using these quiz results.

Subject: {subject}
Available study time per day: {daily_minutes} minutes

Topics and scores:
{topic_details}

Instructions:
1. Prioritize topics with the lowest scores.
2. Use simple English.
3. Create a practical 3-day revision plan.
4. Include study activities and practice questions.
5. Divide each day's activities within the available study time.
6. If scores are strong, suggest ways to improve further.
7. Do not claim that the learner has mastered a topic based only on one score.
"""

    return ask_gemini(prompt)
