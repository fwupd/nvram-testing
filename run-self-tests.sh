#!/bin/sh

export PYTHONDONTWRITEBYTECODE=1

exec python3 -m pytest pytest-selftests.py
