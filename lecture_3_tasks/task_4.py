import argparse
import logging
from collections import defaultdict
from os import getenv
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

try:
	from dotenv import load_dotenv
except ImportError:
	load_dotenv = None


LOGGER = logging.getLogger(__name__)


def init_client(region: str | None = None):
	if load_dotenv is not None:
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


def list_keys(s3_client, bucket_name: str) -> list[str]:
	paginator = s3_client.get_paginator("list_objects_v2")
	keys: list[str] = []
	for page in paginator.paginate(Bucket=bucket_name):
		keys.extend(item["Key"] for item in page.get("Contents", []))
	return keys


def extension_from_key(key: str) -> str:
	suffix = Path(key).suffix.lower().lstrip(".")
	return suffix or "no_extension"


def organize_bucket_by_extension(s3_client, bucket_name: str) -> dict[str, int]:
	counters: dict[str, int] = defaultdict(int)

	for key in list_keys(s3_client, bucket_name):
		if key.endswith("/"):
			continue

		extension = extension_from_key(key)
		file_name = Path(key).name
		new_key = f"{extension}/{file_name}"

		if key == new_key:
			continue

		s3_client.copy_object(
			Bucket=bucket_name,
			CopySource={"Bucket": bucket_name, "Key": key},
			Key=new_key,
		)
		s3_client.delete_object(Bucket=bucket_name, Key=key)
		counters[extension] += 1

	return dict(counters)


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Lecture 3 task 4: organize S3 objects by extension"
	)
	parser.add_argument("--bucket", required=True)
	parser.add_argument("--organize-by-extension", action="store_true")
	parser.add_argument("--region", default=getenv("aws_region_name", "us-west-2"))
	parser.add_argument("--verbose", action="store_true")
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

	if not args.organize_by_extension:
		raise SystemExit("Pass --organize-by-extension to run this operation")

	s3_client = init_client(args.region)
	counters = organize_bucket_by_extension(s3_client, args.bucket)

	if not counters:
		print("No files moved")
		return

	for extension in sorted(counters):
		print(f"{extension} - {counters[extension]}")


if __name__ == "__main__":
	try:
		main()
	except ClientError:
		LOGGER.exception("Organization operation failed")
		raise SystemExit(1) from None
