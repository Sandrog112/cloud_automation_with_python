import argparse
import json
import logging
import mimetypes
from os import getenv
from pathlib import Path

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


def bucket_exists(s3_client, bucket: str) -> bool:
	try:
		s3_client.head_bucket(Bucket=bucket)
		return True
	except ClientError:
		return False


def create_bucket_if_missing(s3_client, bucket: str, region: str) -> None:
	if bucket_exists(s3_client, bucket):
		return
	if region == "us-east-1":
		s3_client.create_bucket(Bucket=bucket)
	else:
		s3_client.create_bucket(
			Bucket=bucket,
			CreateBucketConfiguration={"LocationConstraint": region},
		)


def generate_public_policy(bucket: str) -> str:
	return json.dumps(
		{
			"Version": "2012-10-17",
			"Statement": [
				{
					"Sid": "PublicReadGetObject",
					"Effect": "Allow",
					"Principal": "*",
					"Action": "s3:GetObject",
					"Resource": f"arn:aws:s3:::{bucket}/*",
				}
			],
		}
	)


def configure_website(s3_client, bucket: str) -> None:
	s3_client.delete_public_access_block(Bucket=bucket)
	s3_client.put_bucket_policy(Bucket=bucket, Policy=generate_public_policy(bucket))
	s3_client.put_bucket_website(
		Bucket=bucket,
		WebsiteConfiguration={
			"IndexDocument": {"Suffix": "index.html"},
			"ErrorDocument": {"Key": "index.html"},
		},
	)


def upload_single_file(s3_client, bucket: str, file_path: Path, key: str) -> None:
	mime_type, _ = mimetypes.guess_type(str(file_path))
	extra_args = {"ContentType": mime_type} if mime_type else None
	s3_client.upload_file(
		Filename=str(file_path),
		Bucket=bucket,
		Key=key,
		ExtraArgs=extra_args,
	)


def upload_directory(s3_client, bucket: str, directory: Path) -> int:
	uploaded = 0
	for path in directory.rglob("*"):
		if path.is_file():
			key = str(path.relative_to(directory)).replace("\\", "/")
			upload_single_file(s3_client, bucket, path, key)
			uploaded += 1
	return uploaded


def build_basic_index(first_name: str, last_name: str, output_path: Path) -> None:
	html = (
		"<!doctype html><html><head><meta charset='utf-8'><title>BTU</title></head>"
		f"<body><h1>{first_name} {last_name}</h1></body></html>"
	)
	output_path.write_text(html, encoding="utf-8")


def website_url(bucket: str, region: str) -> str:
	if region == "us-east-1":
		return f"http://{bucket}.s3-website-us-east-1.amazonaws.com"
	return f"http://{bucket}.s3-website-{region}.amazonaws.com"


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Task 4: S3 static website hosting")
	parser.add_argument("--bucket", required=True)
	parser.add_argument("--region", default=getenv("aws_region_name", "us-west-2"))
	parser.add_argument("--basic", action="store_true")
	parser.add_argument("--first-name")
	parser.add_argument("--last-name")
	parser.add_argument("--advanced-react", action="store_true")
	parser.add_argument("--react-dir")
	parser.add_argument("--verbose", action="store_true")
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

	if not args.basic and not args.advanced_react:
		raise SystemExit("Pass --basic or --advanced-react")

	client = init_client(args.region)
	create_bucket_if_missing(client, args.bucket, args.region)

	if args.basic:
		if not args.first_name or not args.last_name:
			raise SystemExit("--first-name and --last-name are required with --basic")
		index_path = Path("index.html")
		build_basic_index(args.first_name, args.last_name, index_path)
		upload_single_file(client, args.bucket, index_path, "index.html")
		configure_website(client, args.bucket)
		print(website_url(args.bucket, args.region))

	if args.advanced_react:
		if not args.react_dir:
			raise SystemExit("--react-dir is required with --advanced-react")
		react_dir = Path(args.react_dir)
		if not react_dir.exists() or not react_dir.is_dir():
			raise SystemExit("--react-dir must point to a valid directory")
		uploaded_count = upload_directory(client, args.bucket, react_dir)
		configure_website(client, args.bucket)
		print(f"Uploaded files: {uploaded_count}")
		print(website_url(args.bucket, args.region))


if __name__ == "__main__":
	try:
		main()
	except ClientError:
		LOGGER.exception("Static hosting operation failed")
		raise SystemExit(1) from None
