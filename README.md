# Cloud Automation With Python

Homework repository for the Cloud Systems Automation With Python course at BTU (Business and Technology University).

This repository contains CLI-based automation tasks across multiple lectures, focused on AWS S3 workflows, policies, versioning, lifecycle rules, static hosting, API integration, and Lambda event processing.

## Repository Layout

```text
cloud_automation_with_python/
	lecture_1_tasks/
		task_1.py
		task_2.py
		task_3.py
	lecture_2_tasks/
		task_1.py
		task_2.py
		task_3.py
		task_4/          # separate Poetry project and separate git repository
	lecture_3_tasks/
		task_1.py
		task_2.py
		task_3.py
		task_4.py
	lecture_4_tasks/
		task_1.py
		task_2.py
		task_3.py
		task_4.py
	lecture_5_tasks/
		task_1.py
		task_2.py
		task_3.py
	.env.example
	pyproject.toml
	uv.lock
```

## Environment Setup

1. Copy .env.example to .env and set AWS credentials.
2. Install dependencies:

```bash
uv sync
```

3. Run scripts from repository root.

Windows note: python-magic may require libmagic runtime support on some systems. If MIME detection fails at runtime, install the required native dependency for your environment.

## Root Environment Variables

The root scripts use these variables:

- aws_access_key_id
- aws_secret_access_key
- aws_session_token (optional)
- aws_region_name

## Running Tasks

Lecture 1:

```bash
python lecture_1_tasks/task_1.py
python lecture_1_tasks/task_2.py "testStringBTu1.23123asd43plm4234"
python lecture_1_tasks/task_3.py 1 a3
```

Lecture 2 (Tasks 1-3):

```bash
python lecture_2_tasks/task_1.py my-bucket-name --region us-east-1
python lecture_2_tasks/task_2.py my-bucket-name --region us-east-1
python lecture_2_tasks/task_3.py my-bucket-name --region us-east-1
```

Lecture 3:

```bash
python lecture_3_tasks/task_1.py --help
python lecture_3_tasks/task_2.py --help
python lecture_3_tasks/task_3.py --help
python lecture_3_tasks/task_4.py --help
```

Lecture 4:

```bash
python lecture_4_tasks/task_1.py --help
python lecture_4_tasks/task_2.py --help
python lecture_4_tasks/task_3.py --help
python lecture_4_tasks/task_4.py --help
```

Lecture 5:

```bash
python lecture_5_tasks/task_1.py --help
python lecture_5_tasks/task_2.py --help
python lecture_5_tasks/task_3.py
```

## Important Note About Lecture 2 Task 4

lecture_2_tasks/task_4 is intentionally treated as a separate project:

1. It has its own pyproject.toml.
2. It uses Poetry.
3. It has its own local .git folder.
4. It should be considered as a separate repository for submission.

See lecture_2_tasks/task_4/README.md for dedicated setup and usage.