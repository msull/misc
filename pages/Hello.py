import streamlit as st

from app_setup import set_page_config

set_page_config("Hello")

from misc_shared.models import Example  # noqa: E402
from misc_shared.storage import get_s3_client  # noqa: E402

client = get_s3_client()
st.write(client.list_buckets())

st.code(Example.create_new({"name": "Test"}).model_dump_json(indent=2))
