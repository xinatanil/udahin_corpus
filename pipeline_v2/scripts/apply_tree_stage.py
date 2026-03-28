#!/usr/bin/env python3
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from identify_collocation import transform_tree as transform_collocation
from identify_synonyms import transform_tree as transform_synonyms
from identify_categories import transform_tree as transform_categories
from identify_minicards import transform_tree as transform_minicards


def main() -> int:
    if len(sys.argv) < 3:
        print('Usage: python3 apply_tree_stage.py <input.xml> <output.xml>')
        return 1

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    tree = ET.parse(input_path)
    transform_collocation(tree)
    transform_synonyms(tree)
    transform_categories(tree)
    transform_minicards(tree)
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
