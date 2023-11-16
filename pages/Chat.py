from datetime import timedelta

import openai
from logzero import logger
from pydantic import Field

from app_setup import set_page_config, st
from misc_shared.storage import get_memory
from misc_shared.streamlit_utils import MemorySessionManager, StreamlitSessionBase

set_page_config(requires_auth=True, page_title="Hello")


class ChatSession(StreamlitSessionBase):
    messages: list = Field(default_factory=list)


def main():
    memory = get_memory()
    session_manager = MemorySessionManager(
        memory=memory,
        model_type=ChatSession,
        logger=logger,
        enable_versioning=False,
        ttl_attribute_name="ttl",
    )

    session: ChatSession = session_manager.init_session(expiration=timedelta(hours=1))

    prompt = st.chat_input("What is up?")

    if st.button("Save Chat Chession to DB"):
        session_manager.persist_session(session)

    with st.expander("Chat Settings"):
        input_cols = iter(st.columns(3))
        with next(input_cols):
            models = get_gpt_models()
            model = st.selectbox("model", models, models.index("gpt-3.5-turbo-1106"))
        with next(input_cols):
            temperature = st.slider("temperature", 0.0, 1.0, 0.5, step=0.1)
        with next(input_cols):
            seed = st.number_input("seed", 0, value=None)

    for message in session.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt:
        session.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for response in openai.chat.completions.create(
                messages=[{"role": m["role"], "content": m["content"]} for m in session.messages],
                model=model,
                temperature=temperature,
                stream=True,
                seed=seed,
            ):
                # for response in openai.completions.create(model='')
                #     model=st.session_state["openai_model"],
                #     messages=[{"role": m["role"], "content": m["content"]} for m in session.messages],
                #     stream=True,
                # ):
                full_response += response.choices[0].delta.content or ""
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        session.messages.append({"role": "assistant", "content": full_response})
        session.save_to_session_state()


@st.cache_data()
def get_gpt_models():
    return sorted(x.id for x in openai.models.list() if "gpt" in x.id)


if __name__ == "__main__":
    main()
