import argparse
import logging
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


def get_versioning_status(s3_client, bucket: str) -> str:
	response = s3_client.get_bucket_versioning(Bucket=bucket)
	return response.get("Status", "Disabled")


def list_versions(s3_client, bucket: str, key: str) -> list[dict]:
	paginator = s3_client.get_paginator("list_object_versions")
	versions: list[dict] = []
	for page in paginator.paginate(Bucket=bucket, Prefix=key):
		for item in page.get("Versions", []):
			if item.get("Key") == key:
				versions.append(item)
	versions.sort(key=lambda item: item["LastModified"], reverse=True)
	return versions


def restore_penultimate_version(s3_client, bucket: str, key: str) -> str | None:
	versions = list_versions(s3_client, bucket, key)
	if len(versions) < 2:
		return None

	source = {
		"Bucket": bucket,
		"Key": key,
		"VersionId": versions[1]["VersionId"],
	}
	response = s3_client.copy_object(Bucket=bucket, Key=key, CopySource=source)
	return response.get("VersionId")


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Task 3: extended versioning management")
	parser.add_argument("--bucket", required=True)
	parser.add_argument("--key")
	parser.add_argument("--check-versioning", action="store_true")
	parser.add_argument("--list-version-history", action="store_true")
	parser.add_argument("--restore-penultimate", action="store_true")
	parser.add_argument("--region", default=getenv("aws_region_name", "us-west-2"))
	parser.add_argument("--verbose", action="store_true")
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

	client = init_client(args.region)

	if args.check_versioning:
		print(get_versioning_status(client, args.bucket))

	if args.list_version_history:
		if not args.key:
			raise SystemExit("--key is required with --list-version-history")
		versions = list_versions(client, args.bucket, args.key)
		print(f"Total versions: {len(versions)}")
		for item in versions:
			print(f"{item['VersionId']} | {item['LastModified']}")

	if args.restore_penultimate:
		if not args.key:
			raise SystemExit("--key is required with --restore-penultimate")
		new_version = restore_penultimate_version(client, args.bucket, args.key)
		if new_version is None:
			print("Not enough versions to restore penultimate")
		else:
			print(f"Restored penultimate version as newest: {new_version}")


if __name__ == "__main__":
	try:
		main()
	except ClientError:
		LOGGER.exception("Versioning operation failed")
		raise SystemExit(1) from None
