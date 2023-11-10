from app_setup import set_page_config, st
from misc_shared.models import Example
from misc_shared.storage import get_s3_client

set_page_config("Hello")

client = get_s3_client()

st.write(client.list_objects_v2(Bucket=st.secrets.app.public_bucket))

st.code(Example.create_new({"name": "Test"}).model_dump_json(indent=2))
