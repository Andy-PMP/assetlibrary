"""Catalog a game asset library into a SQLite database.

Usage:
    python catalog.py <root_dir> [--db assets.db]
"""
import argparse
import os
import sqlite3
import sys
from collections import Counter

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: pip install Pillow")

IMAGE_EXTS = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}
AUDIO_EXTS = {"wav", "mp3", "ogg", "flac"}
BATCH_SIZE = 1000

SCHEMA = """
CREATE TABLE IF NOT EXISTS assets (
    id       INTEGER PRIMARY KEY,
    path     TEXT UNIQUE NOT NULL,
    filename TEXT NOT NULL,
    ext      TEXT NOT NULL,
    folder   TEXT NOT NULL,
    pack     TEXT NOT NULL,
    size_kb  REAL NOT NULL,
    width    INTEGER,
    height   INTEGER,
    kind     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_assets_ext ON assets(ext);
CREATE INDEX IF NOT EXISTS idx_assets_folder ON assets(folder);
"""

INSERT = """
INSERT INTO assets (path, filename, ext, folder, pack, size_kb, width, height, kind)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def kind_for(ext):
    if ext in IMAGE_EXTS:
        return "image"
    if ext in AUDIO_EXTS:
        return "audio"
    return "other"


def image_size(path):
    """Return (width, height) or (None, None) if the image can't be read."""
    try:
        with Image.open(path) as img:  # only reads the header
            return img.size
    except Exception:
        return None, None


def walk(root):
    """Yield one record tuple per file under root."""
    def on_error(err):
        print(f"\nWarning: cannot read {err.filename}: {err.strerror}", file=sys.stderr)

    for dirpath, dirnames, filenames in os.walk(root, onerror=on_error):
        dirnames[:] = [d for d in dirnames if d != "__MACOSX"]  # macOS zip metadata
        rel = os.path.relpath(dirpath, root)
        pack = os.path.basename(root) if rel == "." else rel.split(os.sep)[0]
        folder = os.path.basename(dirpath)
        for name in filenames:
            if name.startswith("._"):  # AppleDouble resource forks, not real files
                continue
            path = os.path.join(dirpath, name)
            try:
                size_kb = round(os.path.getsize(path) / 1024, 2)
            except OSError:
                continue
            ext = os.path.splitext(name)[1].lower().lstrip(".")
            kind = kind_for(ext)
            width = height = None
            if kind == "image":
                width, height = image_size(path)
            yield (path, name, ext, folder, pack, size_kb, width, height, kind)


def main():
    parser = argparse.ArgumentParser(description="Catalog a game asset library into SQLite.")
    parser.add_argument("root", help="Directory to scan recursively")
    parser.add_argument("--db", default="assets.db", help="Output database (default: assets.db)")
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        sys.exit(f"Not a directory: {root}")

    conn = sqlite3.connect(args.db)
    conn.executescript(SCHEMA)

    by_kind, by_ext = Counter(), Counter()
    total_kb = 0.0
    unreadable = 0
    count = 0
    batch = []

    print(f"Scanning {root} ...")
    with conn:  # single transaction: full rescan replaces old contents
        conn.execute("DELETE FROM assets")
        for rec in walk(root):
            batch.append(rec)
            count += 1
            ext, size_kb, width, kind = rec[2], rec[5], rec[6], rec[8]
            by_kind[kind] += 1
            by_ext[ext or "(none)"] += 1
            total_kb += size_kb
            if kind == "image" and width is None:
                unreadable += 1
            if len(batch) >= BATCH_SIZE:
                conn.executemany(INSERT, batch)
                batch.clear()
            if count % 500 == 0:
                print(f"\r  {count:,} files...", end="", flush=True)
        if batch:
            conn.executemany(INSERT, batch)
    conn.close()

    print(f"\r  {count:,} files scanned.   ")
    print()
    print("=== Summary ===")
    print(f"Total files: {count:,}")
    print(f"Total size:  {total_kb / 1024:,.1f} MB")
    print()
    print("By kind:")
    for kind in ("image", "audio", "other"):
        print(f"  {kind:<8}{by_kind[kind]:>10,}")
    print()
    print("By extension:")
    for ext, n in by_ext.most_common():
        print(f"  .{ext:<8}{n:>10,}")
    if unreadable:
        print()
        print(f"Images with unreadable dimensions: {unreadable:,}")
    print()
    print(f"Database written to {os.path.abspath(args.db)}")


if __name__ == "__main__":
    main()
