"""Export assets.db to assets.json (and assets_data.js for the HTML browser).

Usage:
    python export_json.py [--db assets.db] [--out-dir .]

assets_data.js holds the same data as assets.json, wrapped as
`window.ASSETS = [...]`, because browsers block fetch() of local JSON files
from pages opened via file://, but allow <script src>.
"""
import argparse
import json
import os
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

# Tags are keyed by path (not asset id) so they survive catalog.py rescans.
TAGS_SCHEMA = """
CREATE TABLE IF NOT EXISTS tags (
    path TEXT NOT NULL,
    tag  TEXT NOT NULL,
    PRIMARY KEY (path, tag)
) WITHOUT ROWID;
"""


def export(db, out_dir):
    """Write assets.json and assets_data.js from db; return the asset count."""
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.executescript(TAGS_SCHEMA)
    rows = conn.execute("SELECT * FROM assets ORDER BY pack, folder, filename").fetchall()
    tags = defaultdict(list)
    for path, tag in conn.execute("SELECT path, tag FROM tags ORDER BY tag"):
        tags[path].append(tag)
    conn.close()

    assets = []
    for row in rows:
        item = dict(row)
        item["url"] = Path(item["path"]).as_uri()
        item["tags"] = tags.get(item["path"], [])
        assets.append(item)

    data = json.dumps(assets, ensure_ascii=False, separators=(",", ":"))
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "assets.json")
    js_path = os.path.join(out_dir, "assets_data.js")
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(data)
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("window.ASSETS = " + data + ";\n")

    print(f"Exported {len(assets):,} assets to {os.path.abspath(json_path)}")
    print(f"                    and {os.path.abspath(js_path)}")
    return len(assets)


def main():
    parser = argparse.ArgumentParser(description="Export assets.db to JSON.")
    parser.add_argument("--db", default="assets.db", help="Input database (default: assets.db)")
    parser.add_argument("--out-dir", default=".", help="Output directory (default: current)")
    args = parser.parse_args()

    if not os.path.isfile(args.db):
        sys.exit(f"Database not found: {args.db} (run catalog.py first)")
    export(args.db, args.out_dir)


if __name__ == "__main__":
    main()
