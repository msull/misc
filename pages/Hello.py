from app_setup import set_page_config, st
from misc_shared.models import Example
from misc_shared.storage import get_memory, get_s3_client

set_page_config(requires_auth=True, page_title="Hello")

client = get_s3_client()
# st.write(client.list_objects_v2(Bucket=st.secrets.app.private_bucket))

st.subheader("Public")
st.write(
    "\n".join(
        [
            f'* {x["Key"]}'
            for x in client.list_objects_v2(Bucket=st.secrets.app.public_bucket).get("Contents", [{"Key": "None"}])
        ],
    )
)

st.subheader("Private")
st.write(
    "\n".join(
        [
            f'* {x["Key"]}'
            for x in client.list_objects_v2(Bucket=st.secrets.app.private_bucket).get("Contents", [{"Key": "None"}])
        ],
    )
)

memory = get_memory()

resource = memory.get_existing("demo-resource", Example)
if not resource:
    resource = memory.create_new(Example, {"name": "Test"}, override_id="demo-resource")

st.code(resource.model_dump_json(indent=2))
