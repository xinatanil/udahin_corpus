#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from io import BytesIO
import xml.etree.ElementTree as ET

from identify_cross_references import transform_tree as transform_cross_references_tree
from identify_meta import transform_text as transform_meta_text, transform_tree as transform_meta_tree
from identify_trn import TRNProcessor


def main() -> int:
    if len(sys.argv) < 3:
        print('Usage: python3 apply_semantic_stage.py <input.xml> <output.xml>')
        return 1

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    content = input_path.read_text(encoding='utf-8')
    content = transform_meta_text(content)
    root = ET.fromstring(content)
    tree = ET.ElementTree(root)
    transform_meta_tree(tree)
    transform_cross_references_tree(tree)
    processor = TRNProcessor()
    processor.process_tree(tree)

    buffer = BytesIO()
    tree.write(buffer, encoding='UTF-8', xml_declaration=True)
    output_path.write_text(buffer.getvalue().decode('UTF-8'), encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
