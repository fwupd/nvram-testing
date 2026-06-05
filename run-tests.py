#!/usr/bin/env python3

import os
import subprocess
import shutil
import sys
from contextlib import chdir
from pathlib import Path
from urllib.parse import urlparse


def main():
    if "IMAGE" in os.environ:
        image = os.environ.get("IMAGE")
    else:
        image = "https://download.fedoraproject.org/pub/fedora/linux/releases/44/Server/x86_64/images/Fedora-Server-Guest-Generic-44-1.7.x86_64.qcow2"

    img = os.path.basename(urlparse(image).path)

    # integrate it back here
    cur_dir = Path(__file__).parent.resolve()
    if not os.path.isfile(image):
        subprocess.run([cur_dir / "get-reqs.py", "--image", image])

    top = Path(".")
    dirs = sorted(d for d in top.iterdir() if d.is_dir() and not d.name.startswith("."))

    mod_env = os.environ.copy()
    mod_env["PATH"] = ":".join([os.getcwd(), os.environ["PATH"]])

    results = dict()
    failed = 0

    for d in dirs:
        shutil.copy(img, d)
        shutil.copy("DBXUpdate-20241101.x64.bin", d)

        # not thread safe!
        with chdir(d):
            failed_at = []
            commands = [
                ["nvram.py", "extract"],
                ["nvram.py", "build"],
                ["nvram.py", "run", "--image", img],
                ["nvram.py", "compare"],
            ]
            for cmd in commands:
                ret = subprocess.run(
                    cmd,
                    check=False,
                    env=mod_env,
                    capture_output=True,
                    encoding="utf8",
                    timeout=120,
                )
                if ret.returncode != 0:
                    failed_at = [cmd, ret.returncode, ret.stderr]
                    break

            if not failed_at:
                results[d.name] = [True]
            else:
                results[d.name] = [False, *failed_at]
                failed += 1

    for r in results.items():
        if r[1][0]:
            print(f"PASS: {r[0]}")
        else:
            print(f"FAIL: {r[0]} at command: {r[1][1]}")

    if failed:
        for r in results.items():
            print("")
            print(
                f"in dir '{r[0]}', command '{r[1][1]}' failed returning '{r[1][2]}' with error output:"
            )
            print(f"{r[1][3]}")
        sys.exit(1)

    else:
        print("all good!", file=sys.stderr)


if __name__ == "__main__":
    main()
