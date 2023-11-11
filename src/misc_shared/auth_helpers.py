import json
from datetime import timedelta
from typing import Dict, Literal
from uuid import uuid4

import streamlit as st
from cryptography.fernet import Fernet
from logzero import logger
from pydantic import BaseModel
from streamlit_authenticator.authenticate import Authenticate

from misc_shared.storage import get_s3_client


class AuthUser(BaseModel):
    email: str
    name: str
    password: str


class AuthSettings(BaseModel):
    credentials: Dict[Literal["usernames"], Dict[str, AuthUser]]
    cookie_name: str
    key: str
    cookie_expiry_days: int = 30
    preauthorized: dict


def save_auth_db(authenticate: Authenticate):
    logger.info("Saving change to Auth DB")
    credentials_data = {
        "credentials": authenticate.credentials,
        "cookie_name": authenticate.cookie_name,
        "key": authenticate.key,
        "cookie_expiry_days": authenticate.cookie_expiry_days,
        "preauthorized": authenticate.preauthorized,
    }
    # dump, encrypt, put to s3
    dumped = json.dumps(credentials_data)
    encrypted = fernet().encrypt(dumped.encode())

    get_s3_client().put_object(
        Bucket=st.secrets.app.private_bucket, Key="app_data/credentials.json.enc", Body=encrypted
    )
    load_auth_config.clear()


def read_auth_db() -> dict:
    client = get_s3_client()
    try:
        response = client.get_object(Bucket=st.secrets.app.private_bucket, Key="app_data/credentials.json.enc")
    except client.exceptions.NoSuchKey:
        logger.warning("Failed loading auth db from remote storage; may not exist")
        return {}
    decrypted = fernet().decrypt(response["Body"].read())
    loaded = json.loads(decrypted.decode())
    logger.info("Auth DB loaded from remote storage")
    return loaded


@st.cache_resource()
def fernet() -> Fernet:
    return Fernet(st.secrets.app.secret_enc_key)


@st.cache_resource(ttl=timedelta(minutes=5))
def load_auth_config() -> AuthSettings:
    credentials_data = read_auth_db()

    if not credentials_data.get("credentials"):
        logger.warning("No auth database present; loading default authorization data")
        auth_settings = AuthSettings.model_validate(
            {
                "credentials": {"usernames": {}},
                "cookie_name": "dashboard-auth-cookie",
                "key": uuid4().hex,
                "cookie_expiry_days": 30,
                "preauthorized": {"emails": st.secrets.app["allowed_users"].split(",")},
            }
        )
        logger.info("pre-authed users:" + ", ".join(auth_settings.preauthorized["emails"]))
        credentials_data["credentials"] = auth_settings.credentials
        credentials_data["cookie_name"] = auth_settings.cookie_name
        credentials_data["key"] = auth_settings.key
        credentials_data["cookie_expiry_days"] = auth_settings.cookie_expiry_days
        credentials_data["preauthorized"] = auth_settings.preauthorized
    else:
        logger.debug("Loading auth database")
        auth_settings = AuthSettings.model_validate(
            {
                "credentials": credentials_data["credentials"],
                "cookie_name": credentials_data["cookie_name"],
                "key": credentials_data["key"],
                "cookie_expiry_days": credentials_data["cookie_expiry_days"],
                "preauthorized": credentials_data["preauthorized"],
            }
        )

    return auth_settings


def create_authenticator():
    for key in ["authentication_status", "name", "username", "logout", "init"]:
        if key not in st.session_state:
            st.session_state[key] = None
    config = load_auth_config()
    dumped = config.model_dump()
    return Authenticate(
        dumped["credentials"],
        dumped["cookie_name"],
        dumped["key"],
        dumped["cookie_expiry_days"],
        dumped["preauthorized"],
    )


class LoginRequired(RuntimeError):
    pass
