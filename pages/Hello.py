import streamlit as st

from app_setup import set_page_config

set_page_config("Hello")
from misc_shared.models import Example  # noqa: E402

st.write(Example.create_new({"name": "Test"}))