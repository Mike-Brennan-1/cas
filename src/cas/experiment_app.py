import streamlit as st
import time

from cas.open_ai_client import OpenAiClient
client = OpenAiClient()

# Streamed response emulator
def response_generator(text: str):
    
    for word in text.split():
        yield word + " "
        time.sleep(0.05)


st.title("Simple chat")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("How can I help?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        response = st.write_stream(response_generator(client.process_prompt(prompt)))
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})