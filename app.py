import streamlit as st
from main import agent_executor

st.set_page_config(page_title="Ralton Hotel", page_icon="🏨")

if "chat_started" not in st.session_state:
    st.session_state.chat_started = False

if "user_input" not in st.session_state:
    st.session_state.user_input = ""

if "history" not in st.session_state:
    st.session_state.history = []


def process_user_input(user_input):
    clean_input = user_input.strip()

    if clean_input.lower() in ["exit", "quit"]:
        st.session_state.history.append({"role": "user", "content": clean_input})
        feedback_message = """Before you go, we'd love your feedback! 💬

Please take a moment to fill this short feedback form:

➡️ Feedback Form: https://forms.gle/tLBy3Tw4icJZDao99

Thank you for chatting with us. Have a great day!"""
        st.session_state.history.append({"role": "assistant", "content": feedback_message})
        return

    st.session_state.history.append({"role": "user", "content": clean_input})
    chat_history = []
    for entry in st.session_state.history:
        chat_history.append({
            "role": entry["role"],
            "content": entry["content"]
        })

    with st.spinner("Thinking..."):
        response = agent_executor.invoke({
            "chat_history": chat_history,
            "input": clean_input
        })["output"]

    st.session_state.history.append({"role": "assistant", "content": response})

st.markdown("""
    <style>
        body {
            background-color: white;
        }
        .centered {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 90vh;
            flex-direction: column;
            text-align: center;
        }
        .chat-container {
            height: 72vh;
            overflow-y: auto;
            padding: 1rem;
            background-color: white;
            border-top: 1px solid #ddd;
        }
        .chat-bubble {
            padding: 12px 16px;
            border-radius: 20px;
            margin: 10px 0;
            max-width: 75%;
            word-wrap: break-word;
            font-size: 16px;
        }
        .user {
            background-color: #dcf8c6;
            margin-left: auto;
            text-align: right;
        }
        .ai {
            background-color: #f1f0f0;
            margin-right: auto;
            text-align: left;
        }
        textarea {
            width: 100% !important;
            border-radius: 20px;
            padding: 10px;
            resize: none;
            height: 60px;
        }
        .input-row {
            background-color: white;
            padding-top: 10px;
        }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.chat_started:
    st.markdown('<div class="upper_centered">', unsafe_allow_html=True)
    st.markdown("# 🏨 Ralton Hotel Virtual Assistant ")
    st.markdown("## What would you like to ask today?")

    with st.form("input_form"):
        col1, col2= st.columns([8, 1])
        with col1:
            user_input = st.text_area("Ask", label_visibility="collapsed", placeholder="Ask Anything...")
        with col2:
            submit = st.form_submit_button("↑")

        if submit and user_input:
            st.session_state.user_input = user_input
            st.session_state.chat_started = True
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

if st.session_state.user_input:
    process_user_input(st.session_state.user_input)
    st.session_state.user_input = ""

st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for entry in st.session_state.history:
    role = entry["role"]
    msg = entry["content"]
    bubble = "user" if role == "user" else "ai"
    st.markdown(f"<div class='chat-bubble {bubble}'><b>{'You' if role == 'user' else 'Assistant'}:</b><br>{msg}</div>",
                unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

with st.container():
    col1, col2 = st.columns([8, 1])
    with col1:
        user_input = st.text_area("Message", key="chat_input", label_visibility="collapsed",
                                  placeholder="Type your message...")

    with col2:
        if st.button("↑"):
            if user_input.strip():
                process_user_input(user_input)
                st.rerun()
