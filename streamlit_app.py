import streamlit as st
import chime

if st.button('Ding'):
    chime.success()


if st.button('Sync Ding'):
    chime.success(sync=True, raise_error=True)
