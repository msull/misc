import sys
from pathlib import Path
from typing import Optional

import streamlit as st
from logzero import logger
from streamlit.commands.page_config import InitialSideBarState, Layout, MenuItems, PageIcon


class Paths:
    repo_root = Path(__file__).parent
    local_src = repo_root / "src"

    add_to_path = [local_src]


for path in Paths.add_to_path:
    this_path = str(path.absolute())
    if this_path not in sys.path:
        sys.path.insert(0, this_path)


def set_page_config(
    requires_auth: bool = False,
    page_title: Optional[str] = None,
    page_icon: Optional[PageIcon] = None,
    layout: Layout = "centered",
    initial_sidebar_state: InitialSideBarState = "auto",
    menu_items: Optional[MenuItems] = None,
):
    from misc_shared.auth_helpers import LoginRequired, create_authenticator

    st.set_page_config(page_title, page_icon, layout, initial_sidebar_state, menu_items)
    authenticator = create_authenticator()
    st.write(authenticator.credentials)
    st.write(authenticator.preauthorized)

    if requires_auth:
        name, authentication_status, username = authenticator.login("Login", "main")
        if authentication_status is False:
            st.error("Username/password is incorrect")
        elif authentication_status is None:
            st.warning("Please enter your username and password")

        if not authentication_status:
            st.stop()
            raise LoginRequired()
        logger.debug(f"User is authed {name=} {username=}")

    return authenticator


def get_current_user():
    logger.debug(st.session_state)
    return st.session_state.get("name") or "Guest"


def get_current_username():
    return st.session_state.get("username") or "anonymous"
