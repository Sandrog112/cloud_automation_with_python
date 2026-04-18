from dataclasses import dataclass
from os import getenv

from dotenv import load_dotenv


@dataclass(frozen=True)
class AwsConfig:
    aws_access_key_id: str | None
    aws_secret_access_key: str | None
    aws_session_token: str | None
    aws_region_name: str


def load_config() -> AwsConfig:
    load_dotenv()
    return AwsConfig(
        aws_access_key_id=getenv("aws_access_key_id"),
        aws_secret_access_key=getenv("aws_secret_access_key"),
        aws_session_token=getenv("aws_session_token"),
        aws_region_name=getenv("aws_region_name", "us-west-2"),
    )
