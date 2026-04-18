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


def empty_bucket(s3_client, bucket_name: str) -> None:
	paginator = s3_client.get_paginator("list_object_versions")
	for page in paginator.paginate(Bucket=bucket_name):
		to_delete = [
			{"Key": item["Key"], "VersionId": item["VersionId"]}
			for item in page.get("Versions", []) + page.get("DeleteMarkers", [])
		]
		if to_delete:
			s3_client.delete_objects(Bucket=bucket_name, Delete={"Objects": to_delete})

	paginator = s3_client.get_paginator("list_objects_v2")
	for page in paginator.paginate(Bucket=bucket_name):
		to_delete = [{"Key": item["Key"]} for item in page.get("Contents", [])]
		if to_delete:
			s3_client.delete_objects(Bucket=bucket_name, Delete={"Objects": to_delete})


def main() -> None:
	parser = argparse.ArgumentParser()
	parser.add_argument("bucket")
	parser.add_argument("--region", default="us-east-1")
	parser.add_argument("--endpoint-url", default=None)
	args = parser.parse_args()

	s3_client = boto3.client("s3", region_name=args.region, endpoint_url=args.endpoint_url)
	if not bucket_exists(s3_client, args.bucket):
		print(f"Bucket '{args.bucket}' was not found.")
		return

	try:
		s3_client.delete_bucket(Bucket=args.bucket)
	except ClientError as error:
		if str(error.response.get("Error", {}).get("Code", "")) != "BucketNotEmpty":
			raise
		empty_bucket(s3_client, args.bucket)
		s3_client.delete_bucket(Bucket=args.bucket)

	print(f"Bucket '{args.bucket}' deleted.")


if __name__ == "__main__":
	main()
