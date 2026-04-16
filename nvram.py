#!/usr/bin/env python3
"""NVRAM testing build script - Python equivalent of Makefile."""

import argparse
import glob
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse


# Configuration
FWUPDTOOL = "fwupdtool"
IMAGE_URL = "https://download.fedoraproject.org/pub/fedora/linux/releases/42/Server/x86_64/images/Fedora-Server-Guest-Generic-43-1.6.x86_64.qcow2"

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


def build_custom_vars():
    """Build custom_VARS.fd from custom_VARS.builder.xml."""
    xml_path = Path("custom_VARS.builder.xml")
    if not xml_path.exists():
        print("Error: custom_VARS.builder.xml not found. Are you in the correct directory?", file=sys.stderr)
        sys.exit(1)

    # Check all referenced files exist
    tree = ET.parse(xml_path)
    missing = []
    for elem in tree.iter("filename"):
        if elem.text and not Path(elem.text).exists():
            missing.append(elem.text)
    if missing:
        print("Error: missing files referenced in custom_VARS.builder.xml:", file=sys.stderr)
        for f in missing:
            print(f"  {f}", file=sys.stderr)
        sys.exit(1)

    run_cmd([FWUPDTOOL, "firmware-build", "custom_VARS.builder.xml", "custom_VARS.fd"])
    shutil.copy("custom_VARS.fd", "custom_VARS.bak")
    print("Built custom_VARS.fd and created backup")


def get_reqs(image_url: str = IMAGE_URL, copy_in: str | None = None):
    """Download requirements and customize the VM image."""
    parent = Path("..")
    image = image_basename(image_url)

    # Download image if not present
    image_path = parent / image
    if not image_path.exists():
        run_cmd(["curl", "-O", "--output-dir", str(parent), image_url])

    # Copy image to current directory if needed
    local_image = Path(image)
    if not local_image.exists() or (image_path.exists() and image_path.stat().st_mtime > local_image.stat().st_mtime):
        shutil.copy(image_path, image)

    # Customize the image
    virt_cmd: list[str] = [
        "virt-customize",
        "--add", image,
        "--copy-in", "../update-and-shutdown.service:/etc/systemd/system",
        "--link", "../update-and-shutdown.service:/etc/systemd/system/basic.target.wants",
        "--link", "/dev/null:/etc/systemd/system/initial-setup.service",
        "--link", "/dev/null:/etc/systemd/system/systemd-repart.service",
        "--root-password", "password:fwupd",
    ]
    if copy_in is not None and copy_in.strip():
        virt_cmd.extend(["--copy-in", copy_in])
    run_cmd(virt_cmd)

    # Download DBX update CAB
    cab_path = parent / DBX_CAB
    if not cab_path.exists():
        run_cmd(["wget", "-nc", "-P", str(parent), DBX_CAB_URL])

    # Extract CAB
    run_cmd(["gcab", "-x", str(cab_path)])
    print("Requirements ready")


def run_vm(image_url: str = IMAGE_URL, copy_in: str | None = None):
    """Run QEMU with the custom firmware."""
    image = image_basename(image_url)
    # Ensure prerequisites are ready
    if not Path(image).exists():
        get_reqs(image_url, copy_in)
    if not Path("custom_VARS.fd").exists():
        build_custom_vars()

    run_cmd([
        "qemu-system-x86_64",
        "-cpu", "host",
        "-machine", "type=q35,accel=kvm",
        "-m", "4G",
        "-smp", "4",
        "-nic", "user,model=virtio",
        "-drive", "if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE.secboot.fd",
        "-drive", "if=pflash,format=raw,file=custom_VARS.fd",
        "-vnc", ":1",
        image,
    ])


def dump():
    """Dump EFI variables from system."""
    efivars = Path("/sys/firmware/efi/efivars")
    vars_to_dump = [
        "PK-8be4df61-93ca-11d2-aa0d-00e098032b8c",
        "KEK-8be4df61-93ca-11d2-aa0d-00e098032b8c",
        "db-d719b2cb-3d3a-4596-a3bc-dad00e67656f",
        "dbx-d719b2cb-3d3a-4596-a3bc-dad00e67656f",
    ]

    for var in vars_to_dump:
        src = efivars / var
        run_cmd(["dd", f"if={src}", f"of={var}"])

    print("EFI variables dumped")


def extract():
    """Extract firmware signatures from EFI variables."""
    vars_to_extract = [
        "PK-8be4df61-93ca-11d2-aa0d-00e098032b8c",
        "KEK-8be4df61-93ca-11d2-aa0d-00e098032b8c",
        "db-d719b2cb-3d3a-4596-a3bc-dad00e67656f",
    ]

    for var in vars_to_extract:
        run_cmd([FWUPDTOOL, "firmware-extract", var, "efi-signature-list"])

    print("Firmware extracted")


def build_siglist(xml_file: str):
    """Build .siglist from .builder.xml file."""
    if not xml_file.endswith(".builder.xml"):
        print(f"Error: {xml_file} doesn't end with .builder.xml", file=sys.stderr)
        sys.exit(1)

    siglist = xml_file.replace(".builder.xml", ".siglist")
    run_cmd([FWUPDTOOL, "firmware-build", xml_file, siglist])
    print(f"Built {siglist}")


def clean():
    """Remove generated files."""
    patterns = ["*.siglist", "*.fd"]
    removed = []

    for pattern in patterns:
        for f in glob.glob(pattern):
            os.remove(f)
            removed.append(f)

    if removed:
        print(f"Removed: {', '.join(removed)}")
    else:
        print("Nothing to clean")


def compare():
    """Compare old and new firmware."""
    run_cmd(f"{FWUPDTOOL} firmware-export custom_VARS.bak efi-volume > old.txt", shell=True)
    run_cmd(f"{FWUPDTOOL} firmware-export custom_VARS.fd efi-volume > new.txt", shell=True)

    # diff returns non-zero if files differ, which is expected
    result = subprocess.run(["diff", "old.txt", "new.txt"])
    if result.returncode == 0:
        print("No differences found")
    else:
        print("Differences shown above")


def main():
    parser = argparse.ArgumentParser(
        description="NVRAM testing build script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available targets:
  build       Build custom_VARS.fd from custom_VARS.builder.xml
  get_reqs    Download requirements and customize VM image
  run         Run QEMU with custom firmware (builds if needed)
  dump        Dump EFI variables from system
  extract     Extract firmware signatures
  siglist     Build .siglist from .builder.xml file
  clean       Remove generated files (*.siglist, *.fd)
  compare     Compare old and new firmware
""",
    )

    parser.add_argument(
        "target",
        nargs="?",
        help="Target to build",
    )
    parser.add_argument(
        "args",
        nargs="*",
        help="Additional arguments (e.g., XML file for siglist target)",
    )
    parser.add_argument(
        "--image-url",
        default=IMAGE_URL,
        metavar="URL",
        help="VM disk image URL for get_reqs and run (default: built-in Fedora guest image)",
    )
    parser.add_argument(
        "--copy-in",
        default=None,
        metavar="SOURCE:DEST",
        help="Extra virt-customize --copy-in (host path or dir : guest dir); get_reqs and run when it fetches the image",
    )

    args = parser.parse_args()

    if args.target is None:
        parser.print_help()
        sys.exit(0)

    image_url = args.image_url
    copy_in = args.copy_in
    targets = {
        "build": build_custom_vars,
        "custom_vars": build_custom_vars,
        "get_reqs": lambda: get_reqs(image_url, copy_in),
        "run": lambda: run_vm(image_url, copy_in),
        "dump": dump,
        "extract": extract,
        "clean": clean,
        "compare": compare,
    }

    if args.target == "siglist":
        if not args.args:
            print("Error: siglist target requires an XML file argument", file=sys.stderr)
            sys.exit(1)
        build_siglist(args.args[0])
    elif args.target in targets:
        targets[args.target]()
    else:
        print(f"Unknown target: {args.target}", file=sys.stderr)
        print(f"Available targets: {', '.join(targets.keys())}, siglist", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

