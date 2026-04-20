#!/usr/bin/env python3

import pytest
import os
import re


def test_directory_without_whitespace():
    dirs = [
        "    " + d.name
        for d in os.scandir(".")
        if d.is_dir() and re.search(r"\s", d.name)
    ]
    if dirs:
        msg = "\n".join(["directories with whitespace:", *dirs])
        pytest.fail(msg)
