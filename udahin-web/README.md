# Yudakhin Web

Static website version of the Yudakhin dictionary.

## What this contains

- `site/`
  - plain static HTML/CSS/JS
  - GitHub Pages friendly
- `scripts/build_data.py`
  - converts `chatGPT_exp/converted_dict.xml` into:
    - `site/data/index.json`
    - `site/data/entries/*.json`

## Build the web data

From the repo root:

```bash
python3 udahin-web/scripts/build_data.py
```

This reads:

- `chatGPT_exp/converted_dict.xml`

And writes:

- `udahin-web/site/data/index.json`
- `udahin-web/site/data/entries/*.json`

## Run locally

From the repo root:

```bash
cd udahin-web/site
python3 -m http.server 8000
```

Then open:

- `http://localhost:8000`

## GitHub Pages plan

For a separate repo:

1. Create a new repo, for example `udahin-web`.
2. Copy the contents of `udahin-web/site/` into that repo root.
3. Commit and push.
4. In GitHub:
   - `Settings`
   - `Pages`
   - deploy from the default branch root

Because the site uses hash-based navigation, it works fine on GitHub Pages without a backend.

## Notes

- The site does **not** load the full XML in the browser.
- It loads a compact search index first.
- Then it fetches only the bucket that contains the selected entry.
