import argparse
import logging
from os import getenv

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


def get_versioning_status(s3_client, bucket_name: str) -> str:
	response = s3_client.get_bucket_versioning(Bucket=bucket_name)
	return response.get("Status", "Disabled")


def list_file_versions(s3_client, bucket_name: str, key: str) -> list[dict]:
	paginator = s3_client.get_paginator("list_object_versions")
	versions: list[dict] = []
	for page in paginator.paginate(Bucket=bucket_name, Prefix=key):
		for item in page.get("Versions", []):
			if item.get("Key") == key:
				versions.append(item)
	versions.sort(key=lambda item: item["LastModified"], reverse=True)
	return versions


def promote_penultimate_version(s3_client, bucket_name: str, key: str) -> str | None:
	versions = list_file_versions(s3_client, bucket_name, key)
	if len(versions) < 2:
		return None

	penultimate = versions[1]
	copy_source = {
		"Bucket": bucket_name,
		"Key": key,
		"VersionId": penultimate["VersionId"],
	}
	response = s3_client.copy_object(
		Bucket=bucket_name,
		Key=key,
		CopySource=copy_source,
	)
	return response.get("VersionId")


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Lecture 3 task 3: S3 versioning")
	parser.add_argument("--bucket", required=True)
	parser.add_argument("--key")
	parser.add_argument("--check-versioning", action="store_true")
	parser.add_argument("--list-versions", action="store_true")
	parser.add_argument("--promote-penultimate", action="store_true")
	parser.add_argument("--region", default=getenv("aws_region_name", "us-west-2"))
	parser.add_argument("--verbose", action="store_true")
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

	s3_client = init_client(args.region)

	if args.check_versioning:
		print(get_versioning_status(s3_client, args.bucket))

	if args.list_versions:
		if not args.key:
			raise SystemExit("--key is required with --list-versions")
		versions = list_file_versions(s3_client, args.bucket, args.key)
		print(f"Total versions: {len(versions)}")
		for item in versions:
			print(f"{item['VersionId']} | {item['LastModified']}")

	if args.promote_penultimate:
		if not args.key:
			raise SystemExit("--key is required with --promote-penultimate")
		new_version_id = promote_penultimate_version(s3_client, args.bucket, args.key)
		if new_version_id is None:
			print("Not enough versions to promote")
		else:
			print(f"Promoted penultimate version. New version id: {new_version_id}")


if __name__ == "__main__":
	try:
		main()
	except ClientError:
		LOGGER.exception("Versioning operation failed")
		raise SystemExit(1) from None
