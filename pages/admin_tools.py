from app_setup import set_page_config, st
from misc_shared.auth_helpers import load_auth_config
from misc_shared.storage import get_s3_client

authenticator = set_page_config(requires_auth=True, page_title="Hello")

client = get_s3_client()

st.write(authenticator)

if st.button("Wipe Auth"):
    client.delete_object(Bucket=st.secrets.app.private_bucket, Key="app_data/credentials.json.enc")
    authenticator.credentials = {"usernames": {}}
    load_auth_config.clear()
