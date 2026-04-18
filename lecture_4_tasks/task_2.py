import argparse
import logging
from datetime import datetime, timezone
from os import getenv

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv


LOGGER = logging.getLogger(__name__)


def init_client(region: str | None = None):
	load_dotenv()
	client = boto3.client(
		"s3",
		aws_access_key_id=getenv("aws_access_key_id"),
		aws_secret_access_key=getenv("aws_secret_access_key"),
		aws_session_token=getenv("aws_session_token"),
		region_name=region or getenv("aws_region_name", "us-west-2"),
	)
	client.list_buckets()
	return client


def collect_versions_for_key(s3_client, bucket: str, key: str) -> list[dict]:
	paginator = s3_client.get_paginator("list_object_versions")
	versions: list[dict] = []
	for page in paginator.paginate(Bucket=bucket, Prefix=key):
		for item in page.get("Versions", []):
			if item.get("Key") == key:
				versions.append(item)
	return versions


def delete_old_versions(
	s3_client,
	bucket: str,
	keys: list[str],
	months: int,
) -> dict[str, int]:
	now = datetime.now(timezone.utc)
	threshold_days = months * 30
	deleted_per_key: dict[str, int] = {}

	for key in keys:
		deleted = 0
		versions = collect_versions_for_key(s3_client, bucket, key)
		for version in versions:
			age_days = (now - version["LastModified"]).days
			if age_days > threshold_days:
				s3_client.delete_object(
					Bucket=bucket,
					Key=key,
					VersionId=version["VersionId"],
				)
				deleted += 1
		deleted_per_key[key] = deleted
	return deleted_per_key


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Task 2: delete object versions older than N months"
	)
	parser.add_argument("--bucket", required=True)
	parser.add_argument("--keys", nargs="+", required=True)
	parser.add_argument("--months", type=int, default=6)
	parser.add_argument("--region", default=getenv("aws_region_name", "us-west-2"))
	parser.add_argument("--verbose", action="store_true")
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

	client = init_client(args.region)
	result = delete_old_versions(client, args.bucket, args.keys, args.months)
	for key in args.keys:
		print(f"{key} - deleted {result.get(key, 0)}")


if __name__ == "__main__":
	try:
		main()
	except ClientError:
		LOGGER.exception("Version cleanup failed")
		raise SystemExit(1) from None
