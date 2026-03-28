#!/usr/bin/env python3
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from shadow_references import collect_shadow_reference_candidates, format_shadow_reference_report


def main() -> int:
    if len(sys.argv) < 3:
        print('Usage: python3 apply_shadow_reference_stage.py <input.xml> <report.txt>')
        return 1

    input_path = Path(sys.argv[1])
    report_path = Path(sys.argv[2])

    tree = ET.parse(input_path)
    candidates = collect_shadow_reference_candidates(tree)
    report_path.write_text(format_shadow_reference_report(candidates), encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
