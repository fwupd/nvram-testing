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
from lxml import etree


# Configuration
FWUPDTOOL = "fwupdtool"


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
        print(
            "Error: custom_VARS.builder.xml not found. Are you in the correct directory?",
            file=sys.stderr,
        )
        sys.exit(1)

    # Check all referenced files exist
    tree = ET.parse(xml_path)
    missing = []
    for elem in tree.iter("filename"):
        if elem.text and not Path(elem.text).exists():
            missing.append(elem.text)
    if missing:
        print(
            "Error: missing files referenced in custom_VARS.builder.xml:",
            file=sys.stderr,
        )
        for f in missing:
            print(f"  {f}", file=sys.stderr)
        sys.exit(1)

    run_cmd([FWUPDTOOL, "firmware-build", "custom_VARS.builder.xml", "custom_VARS.fd"])
    shutil.copy("custom_VARS.fd", "custom_VARS.bak")
    print("Built custom_VARS.fd and created backup")


def run_vm(image: str):
    """Run QEMU with the custom firmware."""
    if not Path("custom_VARS.fd").exists():
        build_custom_vars()

    run_cmd(
        [
            "qemu-system-x86_64",
            "-cpu",
            "host",
            "-machine",
            "type=q35,accel=kvm",
            "-m",
            "4G",
            "-smp",
            "4",
            "-nic",
            "user,model=virtio",
            "-drive",
            "if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE.secboot.fd",
            "-drive",
            "if=pflash,format=raw,file=custom_VARS.fd",
            "-vnc",
            ":1",
            image,
        ]
    )


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


def _filter_xml(fn_old: str, fn_new: str) -> None:

    with open(fn_old, "rb") as f:
        xml = f.read().decode()
    out_root = etree.Element("firmware", gtype="FuEfiVolume")
    out_varstore = etree.SubElement(
        out_root, "firmware", gtype="FuEfiVss2VariableStore"
    )
    out_authvariable = etree.SubElement(
        out_varstore, "firmware", gtype="FuEfiVssAuthVariable"
    )
    root = etree.fromstring(xml)
    for var in root.xpath(
        "/firmware[@gtype='FuEfiVolume']"
        "/firmware[@gtype='FuEfiVss2VariableStore']"
        "/firmware[@gtype='FuEfiVssAuthVariable']"
    ):
        variable: str = var.xpath("id")[0].text
        if variable not in ["db", "dbx", "KEK", "PK"]:
            continue
        etree.SubElement(out_authvariable, "id", id=variable)
        for certlist in var.xpath("firmware[@gtype='FuEfiSignatureList']"):
            for cert in certlist.xpath("firmware[@gtype='FuEfiX509Signature']"):
                ele_cert = etree.SubElement(
                    out_authvariable, "firmware", gtype="FuEfiX509Signature"
                )
                for key in ["id", "issuer", "subject"]:
                    etree.SubElement(ele_cert, key).text = cert.xpath(key)[0].text
                continue
            for cert in certlist.xpath("firmware[@gtype='FuEfiSignature']"):
                ele_cert = etree.SubElement(
                    out_authvariable, "firmware", gtype="FuEfiSignature"
                )
                for key in ["owner"]:
                    etree.SubElement(ele_cert, key).text = cert.xpath(key)[0].text
                continue
    with open(fn_new, "wb") as f:
        f.write(etree.tostring(out_root, pretty_print=True))


def compare():
    """Compare old and new firmware."""
    run_cmd(
        f"{FWUPDTOOL} firmware-export custom_VARS.fd efi-volume --json > raw.xml",
        shell=True,
    )

    # lets filter this down to only the important stuff
    _filter_xml("raw.xml", "new.xml")

    # diff returns non-zero if files differ, which is expected
    result = subprocess.run(["diff", "aim.xml", "new.xml"])
    if result.returncode == 0:
        print("No differences found")
    else:
        print("Differences shown above")
        sys.exit(1)


def simplify():

    """Simplify the XML to only the interesting parts."""
    _filter_xml("raw.xml", "aim.xml")


def main():
    parser = argparse.ArgumentParser(
        description="NVRAM testing build script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available targets:
  build       Build custom_VARS.fd from custom_VARS.builder.xml
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
        "--image",
        default=None,
        metavar="FILE",
        help="VM disk image filename (required for run)",
    )

    args = parser.parse_args()

    if args.target is None:
        parser.print_help()
        sys.exit(0)

    if args.target == "run" and not args.image:
        print("Error: --image is required for the run target", file=sys.stderr)
        sys.exit(1)

    targets = {
        "build": build_custom_vars,
        "custom_vars": build_custom_vars,
        "run": lambda: run_vm(args.image),
        "dump": dump,
        "extract": extract,
        "clean": clean,
        "compare": compare,
        "simplify": simplify,
    }

    if args.target == "siglist":
        if not args.args:
            print(
                "Error: siglist target requires an XML file argument", file=sys.stderr
            )
            sys.exit(1)
        build_siglist(args.args[0])
    elif args.target in targets:
        targets[args.target]()
    else:
        print(f"Unknown target: {args.target}", file=sys.stderr)
        print(
            f"Available targets: {', '.join(targets.keys())}, siglist", file=sys.stderr
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
