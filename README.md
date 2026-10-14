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
