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


def delete_object(s3_client, bucket_name: str, key: str) -> bool:
	try:
		s3_client.delete_object(Bucket=bucket_name, Key=key)
		return True
	except ClientError:
		LOGGER.exception("Failed to delete object")
		return False


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Lecture 3 task 2: object delete")
	parser.add_argument("--bucket", required=True)
	parser.add_argument("--key", required=True)
	parser.add_argument("-del", "--delete", action="store_true")
	parser.add_argument("--region", default=getenv("aws_region_name", "us-west-2"))
	parser.add_argument("--verbose", action="store_true")
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

	if not args.delete:
		raise SystemExit("Pass -del or --delete to perform deletion")

	s3_client = init_client(args.region)
	ok = delete_object(s3_client, args.bucket, args.key)
	print("deleted" if ok else "not-deleted")


if __name__ == "__main__":
	main()
