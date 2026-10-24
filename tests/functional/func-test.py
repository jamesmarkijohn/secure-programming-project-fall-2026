#!/usr/bin/env python3
"""Runs the functional test suite.

The tests live next to the code they test (src/backend/*/test*.py) and are
tagged "functional". They need Django and PostgreSQL, so this runs them inside
the backend container against a throwaway test database; your real data is
never touched.

Usage (from anywhere in the repo, with `docker compose up` running):
    python3 tests/functional/func-test.py            # run the suite
    python3 tests/functional/func-test.py -v 2       # list each test as it runs
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

command = [
    "docker", "compose", "exec", "-T", "backend",
    "python", "manage.py", "test", "--tag", "functional", *sys.argv[1:],
]

try:
    result = subprocess.run(command, cwd=REPO_ROOT)
except FileNotFoundError:
    sys.exit("Docker isn't installed or isn't on your PATH.")

if result.returncode != 0:
    print("\nIf the error mentions the backend not running, start it with: docker compose up -d",
          file=sys.stderr)
sys.exit(result.returncode)
