import streamlit as st
import pandas as pd
import database
from ai_service import ask_gemini
from quiz_manager import generate_quiz, evaluate_quiz

database.initialize_database()

st.set_page_config(
    page_title="AI Personalized Learning Coach",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 AI Personalized Learning Coach")
st.caption("Create study plans, practise with AI quizzes, and track your progress.")

tab1, tab2, tab3, tab4 = st.tabs([
    "📚 Learning Plan",
    "📝 Practice Quiz",
    "📈 Progress Dashboard",
    "💾 Saved Plans"
])

with tab1:
    st.header("Create Your Learning Plan")

    with st.form("learning_plan_form"):
        subject = st.text_input("Subject", value="Python")
        goal = st.text_input(
            "Your learning goal",
            value="Learn Python programming"
        )
        level = st.selectbox(
            "Your current level",
            ["Beginner", "Intermediate", "Advanced"]
        )
        duration_days = st.number_input(
            "Plan duration (days)", min_value=1, max_value=365, value=30
        )
        daily_minutes = st.number_input(
            "Daily study time (minutes)",
            min_value=10,
            max_value=600,
            value=60
        )
        create_plan = st.form_submit_button("Generate Learning Plan")

    if create_plan:
        if not subject.strip() or not goal.strip():
            st.error("Please enter both subject and learning goal.")
        else:
            prompt = f"""
Create a practical day-wise learning plan.

Subject: {subject}
Goal: {goal}
Level: {level}
Duration: {duration_days} days
Daily study time: {daily_minutes} minutes

Use simple English. Include daily topics, activities, practice tasks,
revision, and a small project when suitable. Format the answer clearly.
"""
            try:
                with st.spinner("Creating your personalized plan..."):
                    plan = ask_gemini(prompt)

                database.save_learning_plan(
                    subject.strip(),
                    goal.strip(),
                    level,
                    int(duration_days),
                    int(daily_minutes),
                    plan
                )
                st.session_state["current_learning_plan"] = plan
                st.success("Your learning plan was saved!")
            except Exception as error:
                st.error(f"Could not create the plan: {error}")

    if st.session_state.get("current_learning_plan"):
        st.markdown(st.session_state["current_learning_plan"])

with tab2:
    st.header("Practice Quiz")

    with st.form("quiz_setup_form"):
        quiz_subject = st.text_input("Quiz subject", value="Python")
        quiz_topic = st.text_input("Topic to practise", value="Variables")
        quiz_level = st.selectbox(
            "Quiz difficulty",
            ["Beginner", "Intermediate", "Advanced"],
            key="quiz_level"
        )
        make_quiz = st.form_submit_button("Generate 5 Questions")

    if make_quiz:
        if not quiz_subject.strip() or not quiz_topic.strip():
            st.error("Please enter a subject and topic.")
        else:
            try:
                with st.spinner("Preparing your quiz..."):
                    questions = generate_quiz(
                        quiz_subject.strip(),
                        quiz_topic.strip(),
                        quiz_level,
                        5
                    )

                st.session_state["active_quiz"] = {
                    "subject": quiz_subject.strip(),
                    "topic": quiz_topic.strip(),
                    "level": quiz_level,
                    "questions": questions
                }
                st.session_state.pop("last_quiz_result", None)
                st.session_state.pop("last_quiz_id", None)
                st.success("Quiz ready! Answer each question below.")
            except Exception as error:
                st.error(f"Could not generate the quiz: {error}")

    active_quiz = st.session_state.get("active_quiz")

    if active_quiz:
        with st.form("answer_quiz_form"):
            answers = {}

            for index, question in enumerate(active_quiz["questions"]):
                st.markdown(f"**Question {index + 1}. {question['question']}**")
                options = question["options"]
                choice = st.radio(
                    f"Choose an answer for question {index + 1}",
                    options=list(options.keys()),
                    format_func=lambda key, opts=options: f"{key}. {opts[key]}",
                    index=None,
                    key=f"answer_{index}"
                )
                answers[str(index)] = choice

            submit_quiz = st.form_submit_button("Submit Answers")

        if submit_quiz:
            try:
                result = evaluate_quiz(active_quiz["questions"], answers)
                result_id = database.save_quiz_result(
                    active_quiz["subject"],
                    active_quiz["topic"],
                    active_quiz["level"],
                    result["score"],
                    result["total"],
                    result["percentage"]
                )
                st.session_state["last_quiz_result"] = result
                st.session_state["last_quiz_id"] = result_id
            except Exception as error:
                st.error(f"Could not save your quiz result: {error}")

    result = st.session_state.get("last_quiz_result")

    if result:
        st.subheader("Your Quiz Result")
        col1, col2 = st.columns(2)
        col1.metric("Score", f"{result['score']} / {result['total']}")
        col2.metric("Percentage", f"{result['percentage']}%")

        if result["percentage"] >= 80:
            st.success("Excellent work! Keep practising.")
        elif result["percentage"] >= 50:
            st.info("Good effort. Review the explanations and try again.")
        else:
            st.warning("Keep learning! Review the topic and practise again.")

        for index, item in enumerate(result["results"], start=1):
            st.markdown(f"**Question {index}:** {item['question']}")
            if item["selected"] == item["correct"]:
                st.success(f"Your answer: {item['selected']} — Correct")
            else:
                st.error(
                    f"Your answer: {item['selected'] or 'Not answered'}"
                )
                st.write(f"Correct answer: {item['correct']}")
            st.write(f"Explanation: {item['explanation']}")

with tab3:
    st.header("Your Progress Dashboard")

    try:
        records = database.get_all_quiz_results()

        if not records:
            st.info(
                "No quiz results yet. Complete a quiz in the Practice Quiz tab "
                "to start tracking your progress."
            )
        else:
            df = pd.DataFrame(records)
            total_quizzes = len(df)
            average_score = float(df["percentage"].mean())
            best_score = float(df["percentage"].max())

            c1, c2, c3 = st.columns(3)
            c1.metric("Quizzes Completed", total_quizzes)
            c2.metric("Average Score", f"{average_score:.1f}%")
            c3.metric("Best Score", f"{best_score:.1f}%")

            st.subheader("Quiz History")
            history_columns = [
                "created_at", "subject", "topic", "level",
                "score", "total", "percentage"
            ]
            st.dataframe(
                df[history_columns].rename(columns={
                    "created_at": "Date",
                    "subject": "Subject",
                    "topic": "Topic",
                    "level": "Level",
                    "score": "Correct Answers",
                    "total": "Total Questions",
                    "percentage": "Score (%)"
                }),
                use_container_width=True,
                hide_index=True
            )

            st.subheader("Average Performance by Topic")
            topic_scores = (
                df.groupby("topic", as_index=False)["percentage"]
                .mean()
                .sort_values("percentage", ascending=False)
            )
            topic_scores["percentage"] = topic_scores["percentage"].round(1)
            st.bar_chart(topic_scores.set_index("topic")["percentage"])

            st.subheader("Topics to Practise More")
            weak_topics = topic_scores[topic_scores["percentage"] < 70]
            if weak_topics.empty:
                st.success(
                    "All your recorded topic averages are at least 70%. "
                    "Keep revising to maintain your progress!"
                )
            else:
                for _, row in weak_topics.iterrows():
                    st.write(
                        f"- **{row['topic']}** — average score "
                        f"{row['percentage']:.1f}%. Try another practice quiz."
                    )

    except Exception as error:
        st.error(f"Could not load your progress: {error}")

with tab4:
    st.header("Saved Learning Plans")

    try:
        plans = database.get_all_learning_plans()

        if not plans:
            st.info("No saved plans yet. Generate a plan in the Learning Plan tab.")
        else:
            for plan in plans:
                with st.expander(
                    f"{plan['subject']} — {plan['goal']} "
                    f"(created {plan['created_at']})"
                ):
                    st.write(f"**Level:** {plan['level']}")
                    st.write(f"**Duration:** {plan['duration_days']} days")
                    st.write(f"**Daily study time:** {plan['daily_minutes']} minutes")
                    st.markdown(plan["plan"])
    except Exception as error:
        st.error(f"Could not load saved plans: {error}")
