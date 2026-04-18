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


def set_public_read_policy(s3_client, bucket: str) -> None:
	policy = json.dumps(
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
	s3_client.delete_public_access_block(Bucket=bucket)
	s3_client.put_bucket_policy(Bucket=bucket, Policy=policy)


def configure_website(s3_client, bucket: str) -> None:
	s3_client.put_bucket_website(
		Bucket=bucket,
		WebsiteConfiguration={
			"IndexDocument": {"Suffix": "index.html"},
			"ErrorDocument": {"Key": "index.html"},
		},
	)


def upload_source_directory(s3_client, bucket: str, source: Path) -> int:
	uploaded_count = 0
	for path in source.rglob("*"):
		if not path.is_file():
			continue
		key = str(path.relative_to(source)).replace("\\", "/")
		mime_type, _ = mimetypes.guess_type(str(path))
		extra_args = {"ContentType": mime_type} if mime_type else None
		s3_client.upload_file(
			Filename=str(path),
			Bucket=bucket,
			Key=key,
			ExtraArgs=extra_args,
		)
		uploaded_count += 1
	return uploaded_count


def website_url(bucket: str, region: str) -> str:
	if region == "us-east-1":
		return f"http://{bucket}.s3-website-us-east-1.amazonaws.com"
	return f"http://{bucket}.s3-website-{region}.amazonaws.com"


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Automated static hosting CLI")
	subparsers = parser.add_subparsers(dest="command", required=True)

	host_parser = subparsers.add_parser("host")
	host_parser.add_argument("bucket")
	host_parser.add_argument("--source", required=True)
	host_parser.add_argument("--region", default=getenv("aws_region_name", "us-west-2"))
	host_parser.add_argument("--verbose", action="store_true")

	return parser.parse_args()


def main() -> None:
	args = parse_args()
	logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

	source = Path(args.source)
	if not source.exists() or not source.is_dir():
		raise SystemExit("--source must be an existing directory")

	client = init_client(args.region)
	create_bucket_if_missing(client, args.bucket, args.region)
	uploaded = upload_source_directory(client, args.bucket, source)
	configure_website(client, args.bucket)
	set_public_read_policy(client, args.bucket)

	print(f"Uploaded files: {uploaded}")
	print(website_url(args.bucket, args.region))


if __name__ == "__main__":
	try:
		main()
	except ClientError:
		LOGGER.exception("Static hosting failed")
		raise SystemExit(1) from None
