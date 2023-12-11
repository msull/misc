import json
from datetime import timedelta

import openai
from logzero import logger
from streamlit_option_menu import option_menu
from supersullytools.streamlit.sessions import MemorySessionManager, StreamlitSessionBase

from app_setup import set_page_config, st
from misc_shared.storage import get_memory

set_page_config(requires_auth=True, page_title="Hello")


class GemmaPageSettings(StreamlitSessionBase):
    some_setting: str = "test"
    updated_count: int = 0


def main():
    selected = option_menu(
        None,
        ["Chat", "Docs", "Debug"],
        icons=["chat", "cloud-upload", "list-task"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
    )
    memory = get_memory()
    session_manager = MemorySessionManager(
        memory=memory,
        model_type=GemmaPageSettings,
        logger=logger,
        enable_versioning=False,
        ttl_attribute_name="ttl",
    )

    session: GemmaPageSettings = session_manager.init_session(expiration=timedelta(days=2))

    # st.write(memory.dynamodb_table.scan())

    match selected:
        case "Chat":
            render_chat(session)
        case "Docs":
            render_docs(session)
        case "Debug":
            render_debug(session, memory, session_manager)
        case _:
            st.error(f"Unexpected option {selected=}")
            raise ValueError(f"Unknown option selected {selected=}")


@st.cache_data()
def get_gpt_models():
    return sorted(x.id for x in openai.models.list() if "gpt" in x.id)


def render_chat(session: GemmaPageSettings):
    pass


def render_docs(session: GemmaPageSettings):
    st.write("render_docs")


def render_debug(session: GemmaPageSettings, memory, session_manager):
    if st.button("Update Count"):
        session.updated_count += 1
        session_manager.persist_session(session)
    if st.button("Set expiration to +1 hour"):
        session_manager.set_session_expiration(session, expiration=timedelta(hours=1))
    if st.button("Set session as expired (-5 minutes)"):
        session_manager.set_session_expiration(session, expiration=timedelta(minutes=-5))

    st.write(f"Session {session.expires_in}.")
    st.subheader("DB Session Dump")
    db_session = session_manager.get_db_session(session.session_id)
    if db_session:
        st.code(db_session.model_dump_json(indent=2, exclude={"session"}))
    else:
        st.write("Session not yet saved")

    st.subheader("Session Dump")
    st.code(session.model_dump_json(indent=2))

    st.subheader("Memory Stats")
    st.code(memory.get_stats().model_dump_json(indent=2))

    st.subheader("Streamlit session state")
    st.code(json.dumps(st.session_state.to_dict(), indent=2, default=str))

    if st.button("Scan Table"):
        items = memory.dynamodb_table.scan().get("Items")
        st.write(list(items))


if __name__ == "__main__":
    main()
