import argparse
import logging
from os import getenv
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

try:
	import magic
except Exception:
	magic = None


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


def resolve_folder_by_mime(mime_type: str) -> str:
	if mime_type.startswith("image/"):
		return "images"
	if mime_type.startswith("video/"):
		return "videos"
	if mime_type.startswith("audio/"):
		return "audio"
	if mime_type.startswith("text/"):
		return "text"
	if mime_type.startswith("application/"):
		return "documents"
	return "other"


def upload_by_content_type(
	s3_client,
	bucket_name: str,
	file_path: str,
	key_name: str | None = None,
) -> str:
	path = Path(file_path)
	if not path.exists() or not path.is_file():
		raise FileNotFoundError(file_path)

	if magic is None:
		raise RuntimeError("python-magic is required for this task")

	mime_type = magic.from_file(str(path), mime=True)
	folder = resolve_folder_by_mime(mime_type)
	final_name = key_name or path.name
	object_key = f"{folder}/{final_name}"

	s3_client.upload_file(
		Filename=str(path),
		Bucket=bucket_name,
		Key=object_key,
		ExtraArgs={"ContentType": mime_type},
	)
	return object_key


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Task 1: detect content-type via python-magic and upload to matching folder"
	)
	parser.add_argument("--bucket", required=True)
	parser.add_argument("--file", required=True)
	parser.add_argument("--key-name")
	parser.add_argument("--region", default=getenv("aws_region_name", "us-west-2"))
	parser.add_argument("--verbose", action="store_true")
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

	client = init_client(args.region)
	key = upload_by_content_type(client, args.bucket, args.file, args.key_name)
	print(key)


if __name__ == "__main__":
	try:
		main()
	except (ClientError, FileNotFoundError, RuntimeError):
		LOGGER.exception("Upload failed")
		raise SystemExit(1) from None
