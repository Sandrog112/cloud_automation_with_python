# AWS S3 Bucket CLI (Task 4)

Production-ready CLI tool for AWS S3 bucket management.

This folder is intentionally a standalone project and should be treated as a separate repository for submission.

## Features

- Initialize AWS S3 client from environment variables
- List, create, delete, and existence-check buckets
- Generate and apply public-read bucket policies
- Read current bucket policy
- Upload supported files from URL after MIME validation
- Set object ACL to public-read

## Required Environment Variables

Copy `.env.example` to `.env` and fill in values:

- `aws_access_key_id`
- `aws_secret_access_key`
- `aws_session_token` (optional)
- `aws_region_name` (default: `us-west-2`)

## Install

```bash
poetry install
```

## Run

```bash
poetry run s3cli --help
```

## Usage

```bash
poetry run s3cli list-buckets
poetry run s3cli create-bucket my-bucket --region us-west-2
poetry run s3cli bucket-exists my-bucket
poetry run s3cli create-bucket-policy my-bucket
poetry run s3cli read-bucket-policy my-bucket
poetry run s3cli set-object-access-policy my-bucket image.jpg
poetry run s3cli upload-from-url my-bucket https://example.com/file.png image.png --keep-local
poetry run s3cli delete-bucket my-bucket --force
```

## Supported Upload File Types

- `.bmp`
- `.jpg`
- `.jpeg`
- `.png`
- `.webp`
- `.mp4`

The tool validates both file extension and detected MIME type before upload.

## Suggested Submission Flow

```bash
git init
git add .
git commit -m "Task 4 solution"
git remote add origin <your-task-4-repo-url>
git push -u origin main
```
