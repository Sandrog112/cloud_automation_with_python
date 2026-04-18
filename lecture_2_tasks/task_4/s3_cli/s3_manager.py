import io
import json
import logging
from pathlib import Path
from urllib.request import urlopen

import boto3
import filetype
from botocore.exceptions import ClientError

from .config import load_config

LOGGER = logging.getLogger(__name__)

_ALLOWED_EXTENSIONS = {
    ".bmp": {"image/bmp", "image/x-ms-bmp"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".png": {"image/png"},
    ".webp": {"image/webp"},
    ".mp4": {"video/mp4"},
}


def init_client():
    config = load_config()
    try:
        client = boto3.client(
            "s3",
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key,
            aws_session_token=config.aws_session_token,
            region_name=config.aws_region_name,
        )
        client.list_buckets()
        LOGGER.info("S3 client initialized successfully")
        return client
    except ClientError:
        LOGGER.exception("Failed to initialize S3 client")
        raise


def list_buckets(aws_s3_client):
    try:
        response = aws_s3_client.list_buckets()
        return [bucket["Name"] for bucket in response.get("Buckets", [])]
    except ClientError:
        LOGGER.exception("Failed to list buckets")
        return []


def create_bucket(aws_s3_client, bucket_name: str, region: str = "us-west-2") -> bool:
    try:
        if region == "us-east-1":
            response = aws_s3_client.create_bucket(Bucket=bucket_name)
        else:
            response = aws_s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region},
            )
    except ClientError:
        LOGGER.exception("Failed to create bucket %s", bucket_name)
        return False
    return response["ResponseMetadata"].get("HTTPStatusCode") == 200


def delete_bucket(aws_s3_client, bucket_name: str) -> bool:
    try:
        response = aws_s3_client.delete_bucket(Bucket=bucket_name)
    except ClientError:
        LOGGER.exception("Failed to delete bucket %s", bucket_name)
        return False
    return response["ResponseMetadata"].get("HTTPStatusCode") == 204


def bucket_exists(aws_s3_client, bucket_name: str) -> bool:
    try:
        response = aws_s3_client.head_bucket(Bucket=bucket_name)
    except ClientError:
        LOGGER.info("Bucket does not exist or is inaccessible: %s", bucket_name)
        return False
    status_code = response["ResponseMetadata"].get("HTTPStatusCode")
    return status_code == 200


def set_object_access_policy(aws_s3_client, bucket_name: str, file_name: str) -> bool:
    try:
        response = aws_s3_client.put_object_acl(
            ACL="public-read",
            Bucket=bucket_name,
            Key=file_name,
        )
    except ClientError:
        LOGGER.exception("Failed to set object ACL for %s/%s", bucket_name, file_name)
        return False
    return response["ResponseMetadata"].get("HTTPStatusCode") == 200


def generate_public_read_policy(bucket_name: str) -> str:
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{bucket_name}/*",
            }
        ],
    }
    return json.dumps(policy)


def create_bucket_policy(aws_s3_client, bucket_name: str) -> bool:
    try:
        aws_s3_client.delete_public_access_block(Bucket=bucket_name)
        aws_s3_client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=generate_public_read_policy(bucket_name),
        )
        LOGGER.info("Bucket policy created for %s", bucket_name)
        return True
    except ClientError:
        LOGGER.exception("Failed to create bucket policy for %s", bucket_name)
        return False


def read_bucket_policy(aws_s3_client, bucket_name: str) -> str | None:
    try:
        policy = aws_s3_client.get_bucket_policy(Bucket=bucket_name)
        return policy.get("Policy")
    except ClientError:
        LOGGER.exception("Failed to read bucket policy for %s", bucket_name)
        return None


def _validate_file_type(file_name: str, content: bytes) -> str:
    extension = Path(file_name).suffix.lower()
    if extension not in _ALLOWED_EXTENSIONS:
        raise ValueError(
            "Unsupported extension. Allowed: .bmp, .jpg, .jpeg, .png, .webp, .mp4"
        )

    kind = filetype.guess(content)
    if kind is None:
        raise ValueError("Could not detect MIME type")

    mime = kind.mime
    if mime not in _ALLOWED_EXTENSIONS[extension]:
        raise ValueError(
            f"MIME type mismatch for {extension}. Detected '{mime}'."
        )

    return mime


def download_file_and_upload_to_s3(
    aws_s3_client,
    bucket_name: str,
    url: str,
    file_name: str,
    keep_local: bool = False,
) -> str:
    LOGGER.info("Downloading file from %s", url)
    with urlopen(url) as response:
        content = response.read()

    mime = _validate_file_type(file_name, content)

    aws_s3_client.upload_fileobj(
        Fileobj=io.BytesIO(content),
        Bucket=bucket_name,
        Key=file_name,
        ExtraArgs={"ContentType": mime},
    )
    LOGGER.info("Uploaded %s to bucket %s", file_name, bucket_name)

    if keep_local:
        Path(file_name).write_bytes(content)
        LOGGER.info("Saved local file %s", file_name)

    return f"https://{bucket_name}.s3.amazonaws.com/{file_name}"


def empty_bucket(aws_s3_client, bucket_name: str) -> bool:
    try:
        versions_paginator = aws_s3_client.get_paginator("list_object_versions")
        for page in versions_paginator.paginate(Bucket=bucket_name):
            version_items = page.get("Versions", []) + page.get("DeleteMarkers", [])
            if version_items:
                objects = [
                    {"Key": item["Key"], "VersionId": item["VersionId"]}
                    for item in version_items
                ]
                aws_s3_client.delete_objects(Bucket=bucket_name, Delete={"Objects": objects})

        objects_paginator = aws_s3_client.get_paginator("list_objects_v2")
        for page in objects_paginator.paginate(Bucket=bucket_name):
            contents = page.get("Contents", [])
            if contents:
                objects = [{"Key": item["Key"]} for item in contents]
                aws_s3_client.delete_objects(Bucket=bucket_name, Delete={"Objects": objects})
        return True
    except ClientError:
        LOGGER.exception("Failed to empty bucket %s", bucket_name)
        return False
