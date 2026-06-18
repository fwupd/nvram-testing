#!/usr/bin/env python3

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def _get_store_el(root: ET.Element, var: str) -> ET.Element | None:
    store = root.find(f".//id[.='{var}']/../firmware[@gtype='FuEfiSignatureList']")
    return store


def _create_variable_store_el(var: str) -> ET.Element:
    guids = {
        "PK": "8be4df61-93ca-11d2-aa0d-00e098032b8c",
        "KEK": "8be4df61-93ca-11d2-aa0d-00e098032b8c",
        "db": "d719b2cb-3d3a-4596-a3bc-dad00e67656f",
        "dbx": "d719b2cb-3d3a-4596-a3bc-dad00e67656f",
    }
    var_attributes = "non-volatile,bootservice-access,runtime-access,time-based-authenticated-write-access"
    assert (
        var in guids
    ), f"Unable to determine GUID for '{var}' variable, known vars are: {', '.join(guids.keys())}"

    var_el = ET.Element("firmware", attrib={"gtype": "FuEfiVssAuthVariable"})
    var_id = ET.SubElement(var_el, "id", {"text": var})
    var_id.text = var
    vendor_guid_el = ET.SubElement(var_el, "vendor_guid")
    vendor_guid_el.text = guids[var]
    attrs_el = ET.SubElement(var_el, "attributes")
    attrs_el.text = var_attributes
    ET.SubElement(var_el, "firmware", attrib={"gtype": "FuEfiSignatureList"})
    return var_el


def parse_xml(input_xml: str) -> dict:
    root = ET.fromstring(input_xml)
    signatures: dict = dict()
    for var in ["PK", "KEK", "db", "dbx"]:
        store_el = _get_store_el(root, var)
        if store_el:
            signatures[var] = []
            for s in store_el.findall("firmware[@gtype='FuEfiX509Signature']"):
                signatures[var].append([s[0].tag, s[0].text])
    return signatures


def build_xml(signatures: dict) -> str:
    """Build a XML describing keys to include in the built nvram image"""
    # signatures: {"PK": [["filename", "pk1.der"], ["filename", "pk2.der"]], "KEK":[], "db":[], "dbx":[]}

    infile = Path(__file__).parent / "custom_VARS.empty.xml"
    out = "custom_VARS.builder.xml"
    sig_type = {
        "PK": "FuEfiX509Signature",
        "KEK": "FuEfiX509Signature",
        "db": "FuEfiX509Signature",
        "dbx": "FuEfiSignature",
    }

    tree = ET.parse(infile)
    root = tree.getroot()
    for s in signatures.items():
        store = root.find(f".//id[.='{s[0]}']/../firmware[@gtype='FuEfiSignatureList']")
        if store is None:
            store_el = root.find(".//firmware[@gtype='FuEfiVss2VariableStore']")
            assert (
                store_el is not None
            ), "The <firmware gtype='FuEfiVss2VariableStore'> element not found!"
            var_el = _create_variable_store_el(s[0])
            store_el.append(var_el)
            store = var_el[-1]
        for signature in s[1]:
            fw_el = ET.Element("firmware", {"gtype": sig_type[s[0]]})
            sig_el = ET.SubElement(fw_el, signature[0])
            sig_el.text = signature[1]
            store.append(fw_el)
    ET.indent(tree)
    return ET.tostring(root, encoding="unicode") + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="A script to build or manipulate XML describing secureboot EFI variables"
    )

    parser.add_argument("--add-pk-file", action="append", help="add PK from this file")
    parser.add_argument(
        "--add-kek-file", action="append", help="add KEK from this file"
    )
    parser.add_argument("--add-db-file", action="append", help="add DB from this file")
    parser.add_argument(
        "--add-dbx-file", action="append", help="add DBX from this file"
    )

    args = parser.parse_args()
    sigs = dict()

    if args.add_pk_file:
        sigs["PK"] = [["filename", f] for f in args.add_pk_file]

    if args.add_kek_file:
        sigs["KEK"] = [["filename", f] for f in args.add_kek_file]

    if args.add_db_file:
        sigs["db"] = [["filename", f] for f in args.add_db_file]

    if args.add_dbx_file:
        sigs["dbx"] = [["filename", f] for f in args.add_dbx_file]

    vars_xml = build_xml(sigs)

    sys.stdout.write(vars_xml)


if __name__ == "__main__":
    main()
