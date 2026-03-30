# pipeline_v2

This folder now has a much narrower job:

- keep the helper scripts and rule files that produce the current golden XML
- keep the golden file itself:
  - `output/converted_dict.xml`
- keep a couple of comparison tools for verification

The active production entrypoint is back under:

- `/Users/xinatanil/Sources/udahin/scripts/convert_source_dict.sh`

That script now uses the proven helper stages from `pipeline_v2/scripts/` so that:

- `chatGPT_exp/converted_dict.xml`
- `pipeline_v2/output/converted_dict.xml`

stay byte-identical.

## What remains here

- `scripts/`: helper stages still used by the main pipeline
- `rules/`: data files used by those helper stages
- `output/converted_dict.xml`: the current golden output
- `tools/compare_against_current.py`: compare two XML outputs
- `tools/diff_cards.py`: card-aware diff
- `run_v2.sh`: optional local rerun of the helper pipeline

## What was removed

Unused experiment/refactor artifacts were deleted:

- neutral-model roundtrip code
- old refactor sandbox code
- stale generated reports and caches
- unused runner code

## Useful commands

Rerun the helper pipeline:

```bash
cd /Users/xinatanil/Sources/udahin/pipeline_v2
./run_v2.sh
```

Compare main output to the golden file:

```bash
cmp -s \
  /Users/xinatanil/Sources/udahin/pipeline_v2/output/converted_dict.xml \
  /Users/xinatanil/Sources/udahin/chatGPT_exp/converted_dict.xml \
  && echo IDENTICAL || echo DIFFERENT
```

Card-aware diff:

```bash
cd /Users/xinatanil/Sources/udahin/pipeline_v2
python3 tools/diff_cards.py \
  --current /Users/xinatanil/Sources/udahin/pipeline_v2/output/converted_dict.xml \
  --candidate /Users/xinatanil/Sources/udahin/chatGPT_exp/converted_dict.xml \
  --ids-only
```
