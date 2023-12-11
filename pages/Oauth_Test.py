# from app_setup import set_page_config, st
import streamlit as st

from misc_shared.st_oauth import st_oauth

# set_page_config(requires_auth=False)
authed = st_oauth()
st.write(authed)
