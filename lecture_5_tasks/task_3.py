import json
import os
from pathlib import Path
from urllib.parse import unquote_plus

import boto3


s3_client = boto3.client("s3")


def extension_from_key(key: str) -> str:
	suffix = Path(key).suffix.lower().lstrip(".")
	return suffix or "no_extension"


def move_object_to_extension_folder(bucket: str, key: str) -> str:
	ext = extension_from_key(key)
	file_name = Path(key).name
	new_key = f"{ext}/{file_name}"

	if key == new_key:
		return new_key

	s3_client.copy_object(
		Bucket=bucket,
		CopySource={"Bucket": bucket, "Key": key},
		Key=new_key,
	)
	s3_client.delete_object(Bucket=bucket, Key=key)
	return new_key


def lambda_handler(event, context):
	moved = []
	for record in event.get("Records", []):
		if record.get("eventSource") != "aws:s3":
			continue

		bucket = record["s3"]["bucket"]["name"]
		key = unquote_plus(record["s3"]["object"]["key"])
		new_key = move_object_to_extension_folder(bucket, key)
		moved.append({"bucket": bucket, "from": key, "to": new_key})

	return {
		"statusCode": 200,
		"body": json.dumps(
			{
				"message": "Processed S3 upload event",
				"moved": moved,
				"required_role": os.getenv("LAMBDA_ROLE_HINT", "LabRole"),
			}
		),
	}

