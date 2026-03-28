#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from refactor.xml_io import load_dictionary, save_dictionary  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description='Roundtrip an XML dictionary through the neutral pipeline_v2 model.')
    parser.add_argument(
        '--input',
        default='/Users/xinatanil/Sources/udahin/chatGPT_exp/converted_dict.xml',
        help='Input XML file',
    )
    parser.add_argument(
        '--output',
        default='/Users/xinatanil/Sources/udahin/pipeline_v2/output/neutral_roundtrip.xml',
        help='Output XML file',
    )
    args = parser.parse_args()

    dictionary = load_dictionary(args.input)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    save_dictionary(dictionary, args.output)
    print(f'Roundtripped {len(dictionary.cards)} cards to {args.output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
