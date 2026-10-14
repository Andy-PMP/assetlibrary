# Asset Browser

Catalog a local game asset library and browse it in a static HTML page — no server needed.

```
pip install Pillow
python catalog.py "D:\GameAssets"      # scan -> assets.db, prints summary
python export_json.py                   # assets.db -> assets.json + assets_data.js
```

Then open `browser.html` in your browser. Keep it in the same folder as `assets_data.js`.

`assets_data.js` contains the same data as `assets.json`, wrapped in a `<script>`-loadable form,
because browsers block reading local JSON files from pages opened via `file://`. If you only have
`assets.json`, the page offers a file picker to load it instead.

Re-run both scripts whenever your library changes (a scan replaces the previous catalog).

## Tags

Add your own tags on any card with **+ tag** (comma-separate several), or use **Tag results…** to
tag everything matching the current search and filter. Tags are searchable like filenames; click a
tag to search for it, or its × to remove it.

Edits save in your browser immediately (shown as "N unsynced"). To store them in `assets.db`:

1. Click **Export tags** — downloads `tags.json`.
2. Run `python import_tags.py` — picks up the newest `tags*.json` in your Downloads folder (or pass
   a path), saves the tags to `assets.db`, and regenerates `assets_data.js`.
3. Reload `browser.html` — the unsynced count clears.

Tags are stored by file path, so they survive rescans. If you move or rename a file, its tags stay
behind under the old path.
