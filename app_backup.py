import streamlit as st
from ai_service import ask_gemini
import database
from quiz_manager import generate_quiz, evaluate_quiz

database.initialize_database()

st.set_page_config(
    page_title="AI Personalized Learning Coach",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 AI Personalized Learning Coach")
st.write(
    "Learn with personalized study plans, AI quizzes, "
    "and saved learning history."
)

tab1, tab2, tab3 = st.tabs([
    "📚 Learning Plan",
    "🧠 Practice Quiz",
    "🗂️ Saved Plans"
])

# ---------------- LEARNING PLAN ----------------
with tab1:
    st.header("Create Your Personalized Learning Plan")

    with st.form("learner_setup"):
        subject = st.text_input(
            "Subject",
            placeholder="Example: Python"
        )
        goal = st.text_input(
            "Learning goal",
            placeholder="Example: Learn Python fundamentals"
        )
        level = st.selectbox(
            "Current level",
            ["Beginner", "Intermediate", "Advanced"]
        )
        duration = st.number_input(
            "Number of days",
            min_value=1,
            max_value=365,
            value=7
        )
        daily_minutes = st.number_input(
            "Daily study time (minutes)",
            min_value=5,
            max_value=720,
            value=45,
            step=5
        )

        submitted = st.form_submit_button(
            "✨ Generate My Learning Plan",
            use_container_width=True
        )

    if submitted:
        if not subject.strip() or not goal.strip():
            st.error("Please enter both subject and learning goal.")
        else:
            prompt = f"""
Create a personalized study plan.

Subject: {subject.strip()}
Goal: {goal.strip()}
Level: {level}
Duration: {int(duration)} days
Daily study time: {int(daily_minutes)} minutes

Give exactly {int(duration)} numbered days.
For each day, include a topic, learning objective,
and practice activity.
Keep the daily work within the time limit.
Use simple English and Markdown.
"""
            try:
                with st.spinner("Generating your learning plan..."):
                    plan = ask_gemini(prompt)

                plan_id = database.save_learning_plan(
                    subject.strip(),
                    goal.strip(),
                    level,
                    int(duration),
                    int(daily_minutes),
                    plan
                )

                st.session_state["generated_plan"] = plan
                st.session_state["current_plan_id"] = plan_id
                st.session_state["subject"] = subject.strip()
                st.session_state["goal"] = goal.strip()
                st.session_state["level"] = level

                st.success("Learning plan generated and saved!")

            except Exception as error:
                st.error("Could not generate or save the learning plan.")
                st.caption(f"Technical details: {error}")

    if "generated_plan" in st.session_state:
        st.divider()
        st.subheader("Your Learning Plan")
        st.markdown(st.session_state["generated_plan"])

# ---------------- PRACTICE QUIZ ----------------
with tab2:
    st.header("🧠 Test Your Knowledge")
    st.write("Generate a quiz, answer the questions, and check your score.")

    default_subject = st.session_state.get("subject", "")
    default_level = st.session_state.get("level", "Beginner")

    with st.form("quiz_setup"):
        quiz_subject = st.text_input(
            "Subject",
            value=default_subject,
            key="quiz_subject"
        )
        topic = st.text_input(
            "Quiz topic",
            placeholder="Example: Python variables",
            key="quiz_topic"
        )
        quiz_level = st.selectbox(
            "Quiz difficulty",
            ["Beginner", "Intermediate", "Advanced"],
            index=["Beginner", "Intermediate", "Advanced"].index(
                default_level
            ),
            key="quiz_level"
        )
        make_quiz = st.form_submit_button(
            "Generate 5 Questions",
            use_container_width=True
        )

    if make_quiz:
        if not quiz_subject.strip() or not topic.strip():
            st.error("Enter both a subject and a topic.")
        else:
            try:
                with st.spinner("Creating your quiz..."):
                    questions = generate_quiz(
                        quiz_subject.strip(),
                        topic.strip(),
                        quiz_level,
                        5
                    )

                st.session_state["quiz_questions"] = questions
                st.session_state["quiz_topic"] = topic.strip()
                st.session_state["quiz_subject_name"] = quiz_subject.strip()
                st.session_state.pop("quiz_result", None)
                st.success("Your quiz is ready!")

            except Exception as error:
                st.error("Could not generate the quiz. Please try again.")
                st.caption(f"Technical details: {error}")

    questions = st.session_state.get("quiz_questions")

    if questions:
        st.subheader(
            f"Quiz: {st.session_state['quiz_topic']}"
        )

        with st.form("answer_quiz"):
            answers = {}

            for index, question in enumerate(questions):
                st.markdown(
                    f"**Question {index + 1}: {question['question']}**"
                )

                options = question["options"]
                selected = st.radio(
                    "Choose one answer:",
                    options=list(options.keys()),
                    format_func=lambda key, opts=options:
                        f"{key}. {opts[key]}",
                    key=f"quiz_answer_{index}",
                    index=None
                )
                answers[str(index)] = selected
                st.divider()

            submitted_quiz = st.form_submit_button(
                "Submit Quiz",
                use_container_width=True
            )

        if submitted_quiz:
            result = evaluate_quiz(questions, answers)
            st.session_state["quiz_result"] = result

        result = st.session_state.get("quiz_result")

        if result:
            st.subheader("Your Quiz Results")
            st.metric(
                "Score",
                f"{result['score']} / {result['total']}"
            )
            st.progress(result["percentage"] / 100)
            st.write(f"Percentage: {result['percentage']}%")

            for index, item in enumerate(result["results"], start=1):
                if item["is_correct"]:
                    st.success(f"Question {index}: Correct!")
                else:
                    st.error(
                        f"Question {index}: Incorrect. "
                        f"Correct answer: {item['correct']}."
                    )

                st.write(item["explanation"])

# ---------------- SAVED PLANS ----------------
with tab3:
    st.header("🗂️ Your Saved Learning Plans")

    try:
        saved_plans = database.get_all_learning_plans()
        st.write(f"Total saved plans: {len(saved_plans)}")

        if not saved_plans:
            st.info("No saved plans yet. Create one in the first tab.")

        for saved_plan in saved_plans:
            title = (
                f"{saved_plan['subject']} — "
                f"{saved_plan['goal']} "
                f"(Plan #{saved_plan['id']})"
            )

            with st.expander(title):
                st.write(f"**Level:** {saved_plan['level']}")
                st.write(
                    f"**Duration:** {saved_plan['duration_days']} days"
                )
                st.write(
                    f"**Daily study time:** "
                    f"{saved_plan['daily_minutes']} minutes"
                )
                st.write(f"**Created:** {saved_plan['created_at']}")
                st.markdown(saved_plan["plan"])

    except Exception as error:
        st.error("Could not load saved plans.")
        st.caption(f"Technical details: {error}")
