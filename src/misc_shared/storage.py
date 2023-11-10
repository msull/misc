from typing import TYPE_CHECKING

import boto3
import streamlit as st
from logzero import logger
from simplesingletable import DynamoDBMemory

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client, S3ServiceResource


@st.cache_resource()
def get_memory() -> DynamoDBMemory:
    return DynamoDBMemory(
        logger=logger,
        table_name=st.secrets["app"]["dynamodb_table"],
        endpoint_url=st.secrets.get("DYNAMODB_ENDPOINT"),
    )


@st.cache_resource
def get_s3_client() -> "S3Client":
    return boto3.client("s3", endpoint_url=st.secrets.get("S3_ENDPOINT"))


@st.cache_resource
def get_s3_resource() -> "S3ServiceResource":
    pass
