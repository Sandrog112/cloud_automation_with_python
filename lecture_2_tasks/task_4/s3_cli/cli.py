import argparse
import json
import logging

from botocore.exceptions import ClientError

from .logging_config import setup_logging
from .s3_manager import (
    bucket_exists,
    create_bucket,
    create_bucket_policy,
    delete_bucket,
    download_file_and_upload_to_s3,
    empty_bucket,
    generate_public_read_policy,
    init_client,
    list_buckets,
    read_bucket_policy,
    set_object_access_policy,
)

LOGGER = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="s3cli")
    parser.add_argument("--verbose", action="store_true")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-buckets")

    create_parser = subparsers.add_parser("create-bucket")
    create_parser.add_argument("bucket")
    create_parser.add_argument("--region", default="us-west-2")

    delete_parser = subparsers.add_parser("delete-bucket")
    delete_parser.add_argument("bucket")
    delete_parser.add_argument("--force", action="store_true")

    exists_parser = subparsers.add_parser("bucket-exists")
    exists_parser.add_argument("bucket")

    object_acl_parser = subparsers.add_parser("set-object-access-policy")
    object_acl_parser.add_argument("bucket")
    object_acl_parser.add_argument("file_name")

    gen_policy_parser = subparsers.add_parser("generate-public-read-policy")
    gen_policy_parser.add_argument("bucket")

    create_policy_parser = subparsers.add_parser("create-bucket-policy")
    create_policy_parser.add_argument("bucket")

    read_policy_parser = subparsers.add_parser("read-bucket-policy")
    read_policy_parser.add_argument("bucket")

    upload_parser = subparsers.add_parser("upload-from-url")
    upload_parser.add_argument("bucket")
    upload_parser.add_argument("url")
    upload_parser.add_argument("file_name")
    upload_parser.add_argument("--keep-local", action="store_true")

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    setup_logging(args.verbose)

    s3_client = init_client()

    if args.command == "list-buckets":
        buckets = list_buckets(s3_client)
        for name in buckets:
            print(name)
        return

    if args.command == "create-bucket":
        status = create_bucket(s3_client, args.bucket, args.region)
        print("created" if status else "not-created")
        return

    if args.command == "delete-bucket":
        if not bucket_exists(s3_client, args.bucket):
            print("bucket-not-found")
            return

        status = delete_bucket(s3_client, args.bucket)
        if not status and args.force:
            if empty_bucket(s3_client, args.bucket):
                status = delete_bucket(s3_client, args.bucket)
        print("deleted" if status else "not-deleted")
        return

    if args.command == "bucket-exists":
        print("exists" if bucket_exists(s3_client, args.bucket) else "not-exists")
        return

    if args.command == "set-object-access-policy":
        status = set_object_access_policy(s3_client, args.bucket, args.file_name)
        print("updated" if status else "not-updated")
        return

    if args.command == "generate-public-read-policy":
        print(json.dumps(json.loads(generate_public_read_policy(args.bucket)), indent=2))
        return

    if args.command == "create-bucket-policy":
        status = create_bucket_policy(s3_client, args.bucket)
        print("created" if status else "not-created")
        return

    if args.command == "read-bucket-policy":
        policy = read_bucket_policy(s3_client, args.bucket)
        print(policy if policy else "not-found")
        return

    if args.command == "upload-from-url":
        try:
            url = download_file_and_upload_to_s3(
                s3_client,
                args.bucket,
                args.url,
                args.file_name,
                keep_local=args.keep_local,
            )
            print(url)
        except (ValueError, ClientError):
            LOGGER.exception("Upload failed")
            raise SystemExit(1) from None


if __name__ == "__main__":
    main()
