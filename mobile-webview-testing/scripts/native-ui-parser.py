#!/usr/bin/env python3
"""
native-ui-parser.py — Parse Android uiautomator XML dumps.

Pulls a UI hierarchy dump from a connected Android device and prints
all clickable elements with their text, bounds, and tap coordinates.

Usage:
    python3 native-ui-parser.py                    # dump + parse
    python3 native-ui-parser.py --tap "Allow"      # find and tap element by text
    python3 native-ui-parser.py --file /tmp/ui.xml  # parse existing dump
"""

import argparse
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass


@dataclass
class NativeElement:
    text: str
    resource_id: str
    class_name: str
    bounds: str
    center_x: int
    center_y: int
    clickable: bool


def parse_bounds(bounds_str: str) -> tuple[int, int]:
    match = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds_str)
    if not match:
        return 0, 0
    x1, y1, x2, y2 = map(int, match.groups())
    return (x1 + x2) // 2, (y1 + y2) // 2


def dump_ui(output_path: str = "/tmp/ui.xml") -> str:
    subprocess.run(
        ["adb", "shell", "uiautomator", "dump", "/data/local/tmp/ui.xml"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["adb", "pull", "/data/local/tmp/ui.xml", output_path],
        check=True,
        capture_output=True,
    )
    return output_path


def parse_xml(xml_path: str) -> list[NativeElement]:
    tree = ET.parse(xml_path)
    elements = []
    for node in tree.iter("node"):
        text = node.get("text", "")
        resource_id = node.get("resource-id", "")
        class_name = node.get("class", "")
        bounds = node.get("bounds", "")
        clickable = node.get("clickable", "false") == "true"

        if not (text or resource_id):
            continue

        cx, cy = parse_bounds(bounds)
        elements.append(
            NativeElement(
                text=text,
                resource_id=resource_id,
                class_name=class_name,
                bounds=bounds,
                center_x=cx,
                center_y=cy,
                clickable=clickable,
            )
        )
    return elements


def tap(x: int, y: int):
    subprocess.run(["adb", "shell", "input", "tap", str(x), str(y)], check=True)


def main():
    parser = argparse.ArgumentParser(description="Parse Android UI hierarchy")
    parser.add_argument("--file", help="Parse an existing XML dump instead of pulling from device")
    parser.add_argument("--tap", metavar="TEXT", help="Find element by text and tap it")
    parser.add_argument("--clickable-only", action="store_true", help="Show only clickable elements")
    args = parser.parse_args()

    xml_path = args.file if args.file else dump_ui()
    elements = parse_xml(xml_path)

    if args.tap:
        matches = [e for e in elements if args.tap.lower() in e.text.lower()]
        if not matches:
            print(f"No element found with text containing '{args.tap}'", file=sys.stderr)
            sys.exit(1)
        target = matches[0]
        print(f"Tapping '{target.text}' at ({target.center_x}, {target.center_y})")
        tap(target.center_x, target.center_y)
        return

    if args.clickable_only:
        elements = [e for e in elements if e.clickable]

    for el in elements:
        click_marker = " [clickable]" if el.clickable else ""
        print(f"({el.center_x:4d}, {el.center_y:4d}) | {el.text or el.resource_id}{click_marker}")
        if el.resource_id and el.text:
            print(f"         id: {el.resource_id}")


if __name__ == "__main__":
    main()
