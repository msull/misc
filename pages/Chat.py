from datetime import timedelta

import openai
from logzero import logger
from pydantic import Field

from app_setup import set_page_config, st
from misc_shared.storage import get_memory
from supersullytools.streamlit.sessions import MemorySessionManager, StreamlitSessionBase
from supersullytools.openai.chat_session import ChatSession

set_page_config(requires_auth=True, page_title="Hello")


class ChatSessionData(StreamlitSessionBase):
    messages: list = Field(default_factory=list)


def main():
    memory = get_memory()
    session_manager = MemorySessionManager(
        memory=memory,
        model_type=ChatSessionData,
        logger=logger,
        enable_versioning=False,
        ttl_attribute_name="ttl",
    )

    session_data: ChatSessionData = session_manager.init_session(expiration=timedelta(hours=1))

    prompt = st.chat_input("What is up?")

    if st.button("Save Chat Chession to DB"):
        session_manager.persist_session(session_data)

    with st.expander("Chat Settings"):
        input_cols = iter(st.columns(3))
        with next(input_cols):
            models = get_gpt_models()
            model = st.selectbox("model", models, models.index("gpt-3.5-turbo-1106"))
        with next(input_cols):
            temperature = st.slider("temperature", 0.0, 1.0, 0.5, step=0.1)
        with next(input_cols):
            seed = st.number_input("seed", 0, value=None)

    for message in session_data.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt:
        chat_session = ChatSession(history=session_data.messages)
        chat_session.user_says(prompt)
        # session_data.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for response in openai.chat.completions.create(
                messages=chat_session.history,
                model=model,
                temperature=temperature,
                stream=True,
                seed=seed,
            ):
                full_response += response.choices[0].delta.content or ""
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

        chat_session.assistant_says(full_response)
        session_data.messages = chat_session.history


@st.cache_data()
def get_gpt_models():
    return sorted(x.id for x in openai.models.list() if "gpt" in x.id)


if __name__ == "__main__":
    main()
