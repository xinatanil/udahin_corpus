#!/usr/bin/env python3
import re
import sys
from pathlib import Path


WORDLINK_RE = re.compile(r'<wordLink(?P<attrs>[^>]*)/?>')
ATTR_RE = re.compile(r'(\w+)="([^"]*)"')
ORDER = ("word", "homonym", "meaning")


def normalize_wordlink_tag(match: re.Match[str]) -> str:
    attrs = dict(ATTR_RE.findall(match.group("attrs")))
    if "word" not in attrs:
        return match.group(0)

    ordered = [f'{name}="{attrs[name]}"' for name in ORDER if name in attrs and attrs[name] != ""]
    return f'<wordLink {" ".join(ordered)}/>'


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: python3 normalize_wordlinks.py <input.xml> <output.xml>")
        return 1

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    content = input_path.read_text(encoding="utf-8")
    content = WORDLINK_RE.sub(normalize_wordlink_tag, content)
    output_path.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
