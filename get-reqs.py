#!/usr/bin/env python3
"""Download requirements and customize the VM image for NVRAM testing."""

import argparse
import os
import requests
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


IMAGE_URL = "https://download.fedoraproject.org/pub/fedora/linux/releases/44/Server/x86_64/images/Fedora-Server-Guest-Generic-44-1.7.x86_64.qcow2"

DBX_CAB_URL = "https://fwupd.org/downloads/093e6913dfecefbdaa9374a2e1caee7bf7e74c7eda847624e456e344884ba5f6-DBXUpdate-20241101-x64.cab"
DBX_CAB = Path(urlparse(DBX_CAB_URL).path).name


def image_basename(image_url: str) -> str:
    """Filename component of the image URL path (e.g. qcow2 name)."""
    return Path(urlparse(image_url).path).name


def run_cmd(cmd: list[str] | str, **kwargs) -> subprocess.CompletedProcess:
    """Run a command and print it first."""
    if isinstance(cmd, list):
        print(f"+ {' '.join(cmd)}")
    else:
        print(f"+ {cmd}")
    return subprocess.run(cmd, check=True, **kwargs)


def download_file(url, target_dir):
    filename = Path(urlparse(url).path.split("/")[-1])
    fullname = target_dir / filename
    chsize = 1024 * 1024
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(fullname, "wb") as f:
            for chunk in r.iter_content(chunk_size=chsize):
                f.write(chunk)
    assert os.path.isfile(fullname)
    return fullname


def get_reqs(
    image_url: str = IMAGE_URL,
    copy_in: str | None = None,
    update_pkgs: bool = False,
):
    """Download requirements and customize the VM image."""
    image = image_basename(image_url)

    # Download image if not present
    if not Path(image).exists():
        download_file(image_url, Path("."))

    # Customize the image
    virt_cmd: list[str] = [
        "virt-customize",
        "--add",
        image,
        "--copy-in",
        "update-and-shutdown.service:/etc/systemd/system",
        "--link",
        "update-and-shutdown.service:/etc/systemd/system/basic.target.wants",
        "--link",
        "/dev/null:/etc/systemd/system/initial-setup.service",
        "--link",
        "/dev/null:/etc/systemd/system/systemd-repart.service",
        "--root-password",
        "password:fwupd",
    ]
    if copy_in is not None and copy_in.strip():
        virt_cmd.extend(["--copy-in", copy_in])
    if update_pkgs:
        virt_cmd.append("--update")
    run_cmd(virt_cmd)

    # Download DBX update CAB
    cab_path = Path(DBX_CAB)
    if not cab_path.exists():
        download_file(DBX_CAB_URL, Path("."))

    # Extract CAB
    run_cmd(["gcab", "-x", DBX_CAB])
    print("Requirements ready")


def main():
    parser = argparse.ArgumentParser(
        description="Download requirements and customize the VM image for NVRAM testing",
    )
    parser.add_argument(
        "--image-url",
        default=IMAGE_URL,
        metavar="URL",
        help="VM disk image URL (default: built-in Fedora guest image)",
    )
    parser.add_argument(
        "--copy-in",
        default=None,
        metavar="SOURCE:DEST",
        help="Extra virt-customize --copy-in (host path or dir : guest dir)",
    )
    parser.add_argument(
        "--update-pkgs",
        action="store_true",
        default=False,
        help="Pass --update to virt-customize to update guest packages",
    )

    args = parser.parse_args()
    get_reqs(args.image_url, args.copy_in, args.update_pkgs)


if __name__ == "__main__":
    main()
