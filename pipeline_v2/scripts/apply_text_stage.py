#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from identify_cross_references import transform_content as transform_cross_references
from identify_alternative_forms import transform_content as transform_alternative_forms


def main() -> int:
    if len(sys.argv) < 3:
        print('Usage: python3 apply_text_stage.py <input.xml> <output.xml>')
        return 1

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    content = input_path.read_text(encoding='utf-8')
    content = transform_cross_references(content)
    content = transform_alternative_forms(content)
    output_path.write_text(content, encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
