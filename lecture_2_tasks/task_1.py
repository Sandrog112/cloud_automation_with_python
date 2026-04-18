import argparse

import boto3
from botocore.exceptions import ClientError


def bucket_exists(s3_client, bucket_name: str) -> bool:
	try:
		s3_client.head_bucket(Bucket=bucket_name)
		return True
	except ClientError as error:
		return str(error.response.get("Error", {}).get("Code", "")) not in {
			"404",
			"NoSuchBucket",
			"NotFound",
		}


def create_bucket(s3_client, bucket_name: str, region: str) -> None:
	if region == "us-east-1":
		s3_client.create_bucket(Bucket=bucket_name)
		return
	s3_client.create_bucket(
		Bucket=bucket_name,
		CreateBucketConfiguration={"LocationConstraint": region},
	)


def main() -> None:
	parser = argparse.ArgumentParser()
	parser.add_argument("bucket")
	parser.add_argument("--region", default="us-east-1")
	parser.add_argument("--endpoint-url", default=None)
	args = parser.parse_args()

	s3_client = boto3.client("s3", region_name=args.region, endpoint_url=args.endpoint_url)
	if bucket_exists(s3_client, args.bucket):
		print(f"Bucket '{args.bucket}' already exists.")
		return

	create_bucket(s3_client, args.bucket, args.region)
	print(f"Bucket '{args.bucket}' created.")


if __name__ == "__main__":
	main()
