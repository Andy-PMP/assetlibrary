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
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Export assets.db to JSON.")
    parser.add_argument("--db", default="assets.db", help="Input database (default: assets.db)")
    parser.add_argument("--out-dir", default=".", help="Output directory (default: current)")
    args = parser.parse_args()

    if not os.path.isfile(args.db):
        sys.exit(f"Database not found: {args.db} (run catalog.py first)")

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM assets ORDER BY pack, folder, filename").fetchall()
    conn.close()

    assets = []
    for row in rows:
        item = dict(row)
        item["url"] = Path(item["path"]).as_uri()
        assets.append(item)

    data = json.dumps(assets, ensure_ascii=False, separators=(",", ":"))
    os.makedirs(args.out_dir, exist_ok=True)
    json_path = os.path.join(args.out_dir, "assets.json")
    js_path = os.path.join(args.out_dir, "assets_data.js")
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(data)
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("window.ASSETS = " + data + ";\n")

    print(f"Exported {len(assets):,} assets to {os.path.abspath(json_path)}")
    print(f"                    and {os.path.abspath(js_path)}")


if __name__ == "__main__":
    main()
