#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from refactor.source_fixes import apply_source_fixes  # noqa: E402


def main() -> int:
    if len(sys.argv) < 3:
        print('Usage: python3 apply_source_fixes.py <input.xml> <output.xml>')
        return 1

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    tree = ET.parse(input_path)
    root = tree.getroot()
    count = apply_source_fixes(root)

    if hasattr(ET, 'indent'):
        ET.indent(tree, space='\t', level=0)
    tree.write(output_path, encoding='UTF-8', xml_declaration=True)
    print(f'Applied {count} source fix(es)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
