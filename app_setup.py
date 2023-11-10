import sys
from pathlib import Path
from typing import Optional

import streamlit as st
from streamlit.commands.page_config import InitialSideBarState, Layout, MenuItems, PageIcon


class Paths:
    repo_root = Path(__file__).parent
    local_src = repo_root / "src"

    add_to_path = [local_src]


def set_page_config(
    page_title: Optional[str] = None,
    page_icon: Optional[PageIcon] = None,
    layout: Layout = "centered",
    initial_sidebar_state: InitialSideBarState = "auto",
    menu_items: Optional[MenuItems] = None,
):
    for path in Paths.add_to_path:
        sys.path.insert(0, str(path.absolute()))

    st.set_page_config(page_title, page_icon, layout, initial_sidebar_state, menu_items)