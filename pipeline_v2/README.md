# pipeline_v2

Isolated rebuild sandbox for the dictionary conversion pipeline.

Goals:
- leave the existing `scripts/` pipeline untouched
- rebuild the conversion flow step by step in a separate folder
- keep the current `chatGPT_exp/converted_dict.xml` as the parity target
- only switch over after the new pipeline reproduces the current output

## Layout
- `scripts/`: copied conversion scripts and XSL files
- `output/`: all v2 outputs and diffs
- `refactor/`: neutral `card / homonym / meaning / line` model and XML IO
- `rules/`: v2-only data files for source fixes and targeted post-fixes
- `tools/compare_against_current.py`: parity checker against the current reference output
- `tools/diff_cards.py`: card-aware diff against the current reference output
- `tools/roundtrip_through_neutral.py`: pass XML through the neutral model and write it back
- `run_v2.sh`: runs the copied pipeline without touching the existing output
- `run_roundtrip.sh`: roundtrips an XML file through the neutral model

## Current boundary
This folder is allowed to diverge freely.
The existing pipeline under `scripts/` and the existing output under `chatGPT_exp/` must remain unchanged.

## Usage
Run the v2 pipeline:

```bash
cd /Users/xinatanil/Sources/udahin/pipeline_v2
./run_v2.sh
```

Compare v2 output against the current reference:

```bash
cd /Users/xinatanil/Sources/udahin/pipeline_v2
python3 tools/compare_against_current.py
```

Compare card-by-card with stable entry IDs:

```bash
cd /Users/xinatanil/Sources/udahin/pipeline_v2
python3 tools/diff_cards.py --limit 10 --diff-lines 60
```

Show only IDs/positions:

```bash
cd /Users/xinatanil/Sources/udahin/pipeline_v2
python3 tools/diff_cards.py --ids-only
```

Filter to one area:

```bash
cd /Users/xinatanil/Sources/udahin/pipeline_v2
python3 tools/diff_cards.py --grep 'баак' --ids-only
```

Show full current vs candidate cards:

```bash
cd /Users/xinatanil/Sources/udahin/pipeline_v2
python3 tools/diff_cards.py --grep 'баак' --view full --limit 1
```

Emit machine-readable JSON:

```bash
cd /Users/xinatanil/Sources/udahin/pipeline_v2
python3 tools/diff_cards.py --grep 'баак' --json --limit 1
```

Roundtrip the current XML through the neutral model:

```bash
cd /Users/xinatanil/Sources/udahin/pipeline_v2
./run_roundtrip.sh
python3 tools/compare_against_current.py --candidate /Users/xinatanil/Sources/udahin/pipeline_v2/output/neutral_roundtrip.xml
```

## Strategy
1. Preserve current behavior first.
2. Measure parity against `chatGPT_exp/converted_dict.xml`.
3. Refactor internals behind the parity harness.
4. Only discuss switching once parity is consistently good.

## Current status
- copied pipeline in `scripts/` already reproduces the current output byte-for-byte
- the neutral-model roundtrip in `refactor/` is structurally identical after XML normalization
- first preservation bug found during refactor: element `tail` text had to be modeled explicitly
- first v2 entry-specific rules now live in `rules/source_fixes.json` and `rules/post_fixes.json`
