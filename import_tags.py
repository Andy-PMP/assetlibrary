"""Merge tags exported from browser.html into assets.db, then re-export.

Usage:
    python import_tags.py [tags.json] [--db assets.db] [--out-dir .] [--no-export]

With no file given, uses the newest tags*.json in your Downloads folder
(browsers save repeat downloads as "tags (1).json", etc.).

Each path in the file has its full tag list replaced, so removals made in the
browser are applied too. Afterwards assets_data.js is regenerated; reload
browser.html and its pending local edits are cleared automatically.
"""
import argparse
import glob
import json
import os
import sqlite3
import sys

from export_json import TAGS_SCHEMA, export


def normalize(tag):
    """Match browser.html: lowercase, trimmed, single spaces."""
    return " ".join(str(tag).lower().split())


def newest_download():
    pattern = os.path.join(os.path.expanduser("~"), "Downloads", "tags*.json")
    files = glob.glob(pattern)
    return max(files, key=os.path.getmtime) if files else None


def main():
    parser = argparse.ArgumentParser(description="Import browser tag edits into assets.db.")
    parser.add_argument("file", nargs="?", help="tags.json exported from browser.html "
                        "(default: newest tags*.json in Downloads)")
    parser.add_argument("--db", default="assets.db", help="Database (default: assets.db)")
    parser.add_argument("--out-dir", default=".", help="Where to re-export JSON (default: current)")
    parser.add_argument("--no-export", action="store_true", help="Skip re-exporting assets_data.js")
    args = parser.parse_args()

    path = args.file or newest_download()
    if not path:
        sys.exit("No tags file given and no tags*.json found in Downloads.")
    if not os.path.isfile(args.db):
        sys.exit(f"Database not found: {args.db} (run catalog.py first)")
    print(f"Reading {os.path.abspath(path)}")

    try:
        with open(path, encoding="utf-8") as f:
            edits = json.load(f)["tags"]
        if not isinstance(edits, dict):
            raise ValueError("'tags' must be an object")
    except (OSError, ValueError, KeyError, TypeError) as e:
        sys.exit(f"Not a valid tags export: {e}")

    conn = sqlite3.connect(args.db)
    conn.executescript(TAGS_SCHEMA)
    known = {p for (p,) in conn.execute("SELECT path FROM assets")}
    added = 0
    with conn:
        for asset_path, tags in edits.items():
            clean = sorted({normalize(t) for t in tags} - {""})
            conn.execute("DELETE FROM tags WHERE path = ?", (asset_path,))
            conn.executemany("INSERT INTO tags (path, tag) VALUES (?, ?)",
                             [(asset_path, t) for t in clean])
            added += len(clean)
    total = conn.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
    conn.close()

    unknown = sum(1 for p in edits if p not in known)
    print(f"Updated tags on {len(edits):,} assets ({added:,} tags). "
          f"Database now has {total:,} tags.")
    if unknown:
        print(f"Note: {unknown:,} paths aren't in the current catalog (moved or renamed?); "
              "their tags were kept.")

    if not args.no_export:
        export(args.db, args.out_dir)
        print("Reload browser.html to see the synced tags.")


if __name__ == "__main__":
    main()
