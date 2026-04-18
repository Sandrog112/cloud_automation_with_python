import argparse
import logging
import mimetypes
from os import getenv
from pathlib import Path

import boto3
from boto3.s3.transfer import TransferConfig
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


def bucket_exists(s3_client, bucket_name: str) -> bool:
	try:
		s3_client.head_bucket(Bucket=bucket_name)
		return True
	except ClientError:
		return False


def create_bucket(s3_client, bucket_name: str, region: str) -> bool:
	try:
		if region == "us-east-1":
			s3_client.create_bucket(Bucket=bucket_name)
		else:
			s3_client.create_bucket(
				Bucket=bucket_name,
				CreateBucketConfiguration={"LocationConstraint": region},
			)
		return True
	except ClientError:
		LOGGER.exception("Failed to create bucket")
		return False


def list_buckets(s3_client) -> list[str]:
	response = s3_client.list_buckets()
	return [bucket["Name"] for bucket in response.get("Buckets", [])]


def delete_bucket(s3_client, bucket_name: str) -> bool:
	try:
		s3_client.delete_bucket(Bucket=bucket_name)
		return True
	except ClientError:
		LOGGER.exception("Failed to delete bucket")
		return False


def validate_mimetype(file_path: str) -> str:
	guessed_mime, _ = mimetypes.guess_type(file_path)
	if not guessed_mime:
		raise ValueError(f"Could not detect mimetype for '{file_path}'")
	return guessed_mime


def small_file_upload(
	s3_client,
	bucket_name: str,
	file_path: str,
	object_key: str,
	check_mimetype: bool,
) -> bool:
	try:
		extra_args = {}
		if check_mimetype:
			extra_args["ContentType"] = validate_mimetype(file_path)

		file_bytes = Path(file_path).read_bytes()
		s3_client.put_object(
			Bucket=bucket_name,
			Key=object_key,
			Body=file_bytes,
			**({"ContentType": extra_args["ContentType"]} if extra_args else {}),
		)
		return True
	except (ClientError, OSError, ValueError):
		LOGGER.exception("Small upload failed")
		return False


def multipart_upload(
	s3_client,
	bucket_name: str,
	file_path: str,
	object_key: str,
	check_mimetype: bool,
) -> bool:
	try:
		extra_args = {}
		if check_mimetype:
			extra_args["ContentType"] = validate_mimetype(file_path)

		config = TransferConfig(
			multipart_threshold=8 * 1024 * 1024,
			multipart_chunksize=8 * 1024 * 1024,
			max_concurrency=4,
			use_threads=True,
		)
		s3_client.upload_file(
			Filename=file_path,
			Bucket=bucket_name,
			Key=object_key,
			ExtraArgs=extra_args or None,
			Config=config,
		)
		return True
	except (ClientError, OSError, ValueError):
		LOGGER.exception("Multipart upload failed")
		return False


def apply_lifecycle_policy(
	s3_client,
	bucket_name: str,
	days: int = 120,
	prefix: str = "",
) -> bool:
	try:
		s3_client.put_bucket_lifecycle_configuration(
			Bucket=bucket_name,
			LifecycleConfiguration={
				"Rules": [
					{
						"ID": f"expire-after-{days}-days",
						"Status": "Enabled",
						"Filter": {"Prefix": prefix},
						"Expiration": {"Days": days},
					}
				]
			},
		)
		return True
	except ClientError:
		LOGGER.exception("Failed to apply lifecycle policy")
		return False


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Lecture 3 task 1 S3 CLI")
	parser.add_argument("--region", default=getenv("aws_region_name", "us-west-2"))
	parser.add_argument("--bucket")
	parser.add_argument("--list-buckets", action="store_true")
	parser.add_argument("--create-bucket", action="store_true")
	parser.add_argument("--delete-bucket", action="store_true")
	parser.add_argument("--small-upload", metavar="FILE_PATH")
	parser.add_argument("--large-upload", metavar="FILE_PATH")
	parser.add_argument("--object-key")
	parser.add_argument("--validate-mimetype", action="store_true")
	parser.add_argument("--set-lifecycle-policy", action="store_true")
	parser.add_argument("--lifecycle-days", type=int, default=120)
	parser.add_argument("--lifecycle-prefix", default="")
	parser.add_argument("--verbose", action="store_true")
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

	client = init_client(args.region)

	if args.list_buckets:
		for bucket in list_buckets(client):
			print(bucket)

	needs_bucket = any(
		[
			args.create_bucket,
			args.delete_bucket,
			args.small_upload,
			args.large_upload,
			args.set_lifecycle_policy,
		]
	)
	if needs_bucket and not args.bucket:
		raise SystemExit("--bucket is required for this operation")

	if args.create_bucket:
		if bucket_exists(client, args.bucket):
			print(f"Bucket '{args.bucket}' already exists.")
		else:
			print("Bucket created." if create_bucket(client, args.bucket, args.region) else "Bucket was not created.")

	if args.delete_bucket:
		print("Bucket deleted." if delete_bucket(client, args.bucket) else "Bucket was not deleted.")

	if args.small_upload:
		if not args.object_key:
			raise SystemExit("--object-key is required for uploads")
		ok = small_file_upload(
			client,
			args.bucket,
			args.small_upload,
			args.object_key,
			args.validate_mimetype,
		)
		print("Small upload complete." if ok else "Small upload failed.")

	if args.large_upload:
		if not args.object_key:
			raise SystemExit("--object-key is required for uploads")
		ok = multipart_upload(
			client,
			args.bucket,
			args.large_upload,
			args.object_key,
			args.validate_mimetype,
		)
		print("Multipart upload complete." if ok else "Multipart upload failed.")

	if args.set_lifecycle_policy:
		ok = apply_lifecycle_policy(
			client,
			args.bucket,
			days=args.lifecycle_days,
			prefix=args.lifecycle_prefix,
		)
		print("Lifecycle policy applied." if ok else "Lifecycle policy failed.")


if __name__ == "__main__":
	try:
		main()
	except ClientError:
		LOGGER.exception("AWS operation failed")
		raise SystemExit(1) from None
