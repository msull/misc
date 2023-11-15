import json
from datetime import timedelta

from logzero import logger
from streamlit_option_menu import option_menu

from app_setup import set_page_config, st
from misc_shared.storage import get_memory
from misc_shared.streamlit_utils import MemorySessionManager, StreamlitSessionBase

set_page_config(requires_auth=True, page_title="Hello")


class GemmaPageSettings(StreamlitSessionBase):
    some_setting: str = "test"


def main():
    memory = get_memory()
    session_manager = MemorySessionManager(
        memory=memory,
        model_type=GemmaPageSettings,
        logger=logger,
        enable_versioning=False,
        ttl_attribute_name="ttl",
    )

    session: GemmaPageSettings = session_manager.init_session(expiration=timedelta(seconds=30))
    session.some_setting = "Updated test"
    session_manager.persist_session(session)

    # st.write(memory.dynamodb_table.scan())
    selected = option_menu(
        None,
        ["Chat", "Docs", "Debug"],
        icons=["chat", "cloud-upload", "list-task"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
    )
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


def render_chat(session: GemmaPageSettings):
    st.write(f"Session {session.expires_in}.")


def render_docs(session: GemmaPageSettings):
    st.write("render_docs")


def render_debug(session: GemmaPageSettings, memory, session_manager):
    db_session = session_manager._get_db_session(session.session_id)
    st.subheader("DB Session Dump")
    st.code(db_session.model_dump_json(indent=2, exclude={"session"}))
    st.subheader("Session Dump")
    st.code(session.model_dump_json(indent=2))
    st.subheader("Memory Stats")
    st.code(memory.get_stats().model_dump_json(indent=2))
    st.subheader("Streamlit session state")
    st.code(json.dumps(st.session_state.to_dict(), indent=2, default=str))


if __name__ == "__main__":
    main()
