#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from identify_cross_references import transform_plain_reference_xrs


def main() -> int:
    if len(sys.argv) < 3:
        print('Usage: python3 apply_pre_links_xr_stage.py <input.xml> <output.xml>')
        return 1

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    content = input_path.read_text(encoding='utf-8')
    content = transform_plain_reference_xrs(content)
    output_path.write_text(content, encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
