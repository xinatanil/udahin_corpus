#!/usr/bin/env python3
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from identify_cross_references import transform_tree as transform_cross_references
from identify_alternative_forms import transform_tree as transform_alternative_forms


def main() -> int:
    if len(sys.argv) < 3:
        print('Usage: python3 apply_post_links_tree_stage.py <input.xml> <output.xml>')
        return 1

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    tree = ET.parse(input_path)
    transform_cross_references(tree)
    transform_alternative_forms(tree)
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
