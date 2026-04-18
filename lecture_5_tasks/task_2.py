import argparse
import json
import logging
from datetime import datetime, timezone
from os import getenv
from urllib.parse import quote_plus
from urllib.request import urlopen

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


def fetch_quote(author: str | None = None) -> dict:
	base_url = "https://api.quotable.io/random"
	url = base_url if not author else f"{base_url}?author={quote_plus(author)}"
	with urlopen(url) as response:
		payload = response.read().decode("utf-8")
	data = json.loads(payload)
	return {
		"author": data.get("author"),
		"content": data.get("content"),
		"tags": data.get("tags", []),
		"id": data.get("_id"),
	}


def save_quote_to_s3(s3_client, bucket: str, quote_payload: dict) -> str:
	timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
	key = f"quotes/quote_{timestamp}.json"
	s3_client.put_object(
		Bucket=bucket,
		Key=key,
		Body=json.dumps(quote_payload, ensure_ascii=False, indent=2).encode("utf-8"),
		ContentType="application/json",
	)
	return key


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Quote CLI with S3 save")
	parser.add_argument("bucket", nargs="?")
	parser.add_argument("--inspire", nargs="?", const="", default=None)
	parser.add_argument("-save", "--save", action="store_true")
	parser.add_argument("--region", default=getenv("aws_region_name", "us-west-2"))
	parser.add_argument("--verbose", action="store_true")
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

	if args.inspire is None:
		raise SystemExit("Pass --inspire or --inspire \"Author Name\"")

	author = args.inspire.strip() or None
	quote_payload = fetch_quote(author)
	print(json.dumps(quote_payload, ensure_ascii=False, indent=2))

	if args.save:
		if not args.bucket:
			raise SystemExit("Bucket name is required when using --save")
		client = init_client(args.region)
		key = save_quote_to_s3(client, args.bucket, quote_payload)
		print(f"Saved to s3://{args.bucket}/{key}")


if __name__ == "__main__":
	try:
		main()
	except ClientError:
		LOGGER.exception("S3 save failed")
		raise SystemExit(1) from None
