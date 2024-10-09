import streamlit as st
import time
import uuid
from retriever import get_answer
from db import save_conversation, save_feedback
import json
import random


def print_log(message):
    print(message, flush=True)


def main():
    print_log("Starting the /r/Germany Wiki Helper")
    st.title("/r/Germany Wiki Helper")
    st.markdown(
        """


        The **/r/Germany wiki pages** offer a comprehensive resource for anyone
        living in or planning to move to Germany. They cover important topics
        ranging from education (university, Studienkolleg) and housing options
        to the tax system, work, and visa processes. Valuable information is
        available on everyday life in Germany, culture, insurance, language
        learning, and much more.
        Popular sections include:

        - **Education & University**: Everything you need to know about studying in Germany.
        - **Housing & Renting**: How to find and rent a home.
        - **Visa & Residency**: Visa types and residency applications.
        - **Tax & Finance**: Managing taxes and finances in Germany.
        - **Language Learning**: Resources to improve German language skills.
        - **Working**: Job opportunities and the German job market.

        Whether for short-term or long-term plans, these pages serve as a helpful guide.

    """
    )

    with open("docs_with_q_4o-mini.json", "rt") as f_in:
        ds_gpt = json.load(f_in)

    rd = random.choice(ds_gpt)
    st.markdown(f"**Example Q**:{rd['question']}")
    st.markdown(f"Source: {rd['source']}")

    # Session state initialization
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = str(uuid.uuid4())
        print_log(
            f"New conversation started with ID: {st.session_state.conversation_id}"
        )
    if "count" not in st.session_state:
        st.session_state.count = 0
        print_log("Feedback count initialized to 0")

    # User input
    user_input = st.text_input("Enter your question:")

    if st.button("Ask"):
        print_log(f"User asked: '{user_input}'")
        with st.spinner("Processing..."):
            start_time = time.time()
            output = get_answer(user_input)
            answer = output["answer"]
            source = output["metas"]["source"]
            end_time = time.time()
            print_log(f"Answer received in {end_time - start_time:.2f} seconds")
            st.success("Completed!")

            if output["eval_score"] == 1:
                st.markdown(answer)
                st.markdown(f"""[Source Wiki]({source})""")
            else:
                st.write("Sorry, I can't find answer in Wiki database")

            print_log("Saving conversation to database")
            save_conversation(st.session_state.conversation_id, user_input, output)
            print_log("Conversation saved successfully")

    # Feedback buttons
    col = st.columns(1)
    with col[0]:

        sentiment_mapping = [1, 2, 3, 4, 5]
        selected = st.feedback("stars")
        if selected is not None:
            if selected == 1:
                st.markdown(f"You selected {sentiment_mapping[selected]} star(s)")
                save_feedback(st.session_state.conversation_id, 1)
            elif selected == 2:
                st.markdown(f"You selected {sentiment_mapping[selected]} star(s)")
                save_feedback(st.session_state.conversation_id, 2)
            elif selected == 3:
                st.markdown(f"You selected {sentiment_mapping[selected]} star(s)")
                save_feedback(st.session_state.conversation_id, 3)
            elif selected == 4:
                st.markdown(f"You selected {sentiment_mapping[selected]} star(s)")
                save_feedback(st.session_state.conversation_id, 4)
            else:
                st.markdown(f"You selected {sentiment_mapping[selected]} star(s)")
                save_feedback(st.session_state.conversation_id, 5)
    print_log("Streamlit app loop completed")


if __name__ == "__main__":
    print_log("Wiki Helper application started")
    main()
