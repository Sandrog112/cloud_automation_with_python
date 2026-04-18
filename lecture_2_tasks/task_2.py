import argparse
import json

import boto3
from botocore.exceptions import ClientError


def build_policy(bucket_name: str) -> dict:
	return {
		"Version": "2012-10-17",
		"Statement": [
			{
				"Sid": "PublicReadDevPrefix",
				"Effect": "Allow",
				"Principal": "*",
				"Action": ["s3:GetObject"],
				"Resource": [f"arn:aws:s3:::{bucket_name}/dev/*"],
			},
			{
				"Sid": "PublicReadTestPrefix",
				"Effect": "Allow",
				"Principal": "*",
				"Action": ["s3:GetObject"],
				"Resource": [f"arn:aws:s3:::{bucket_name}/test/*"],
			},
		],
	}


def main() -> None:
	parser = argparse.ArgumentParser()
	parser.add_argument("bucket")
	parser.add_argument("--region", default="us-east-1")
	parser.add_argument("--endpoint-url", default=None)
	parser.add_argument("--disable-public-block", action="store_true")
	args = parser.parse_args()

	s3_client = boto3.client("s3", region_name=args.region, endpoint_url=args.endpoint_url)
	try:
		s3_client.get_bucket_policy(Bucket=args.bucket)
		print(f"Bucket policy for '{args.bucket}' already exists.")
		return
	except ClientError as error:
		error_code = str(error.response.get("Error", {}).get("Code", ""))
		if error_code not in {"NoSuchBucketPolicy", "NoSuchBucket", "404", "NotFound"}:
			raise
		if error_code in {"NoSuchBucket", "404", "NotFound"}:
			print(f"Bucket '{args.bucket}' was not found.")
			return

	if args.disable_public_block:
		s3_client.put_public_access_block(
			Bucket=args.bucket,
			PublicAccessBlockConfiguration={
				"BlockPublicAcls": False,
				"IgnorePublicAcls": False,
				"BlockPublicPolicy": False,
				"RestrictPublicBuckets": False,
			},
		)

	policy = build_policy(args.bucket)
	try:
		s3_client.put_bucket_policy(Bucket=args.bucket, Policy=json.dumps(policy))
	except ClientError as error:
		error_code = str(error.response.get("Error", {}).get("Code", ""))
		if error_code in {"AccessDenied", "AllAccessDisabled"}:
			print(
				"Could not apply public policy due to public-access restrictions. "
				"Retry with --disable-public-block if your account allows it."
			)
			return
		raise

	print(f"Bucket policy for '{args.bucket}' created.")


if __name__ == "__main__":
	main()
