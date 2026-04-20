#!/usr/bin/env python3

import pytest
import os
import re
import subprocess


def run_cmd(cmd):
    return subprocess.run(
        cmd,
        capture_output=True,
        encoding="utf-8",
    )


def test_directory_without_whitespace():
    dirs = [
        "    " + d.name
        for d in os.scandir(".")
        if d.is_dir() and re.search(r"\s", d.name)
    ]
    if dirs:
        msg = "\n".join(["directories with whitespace:", *dirs])
        pytest.fail(msg)


def test_format_python():
    res = run_cmd(["black", "--check", "."])
    if res.returncode != 0:
        pytest.fail(res.stderr)
