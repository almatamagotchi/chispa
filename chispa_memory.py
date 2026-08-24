#!/usr/bin/env python3
"""
chispa_memory.py — chispa's own memory files.

daily observations live in memory/MEMORY-YYYY-MM-DD.md; the compressed
index lives in memory/MEMORY.md. nothing here touches the main workspace
pipeline — this is the valley's own small garden.
"""

import os
from datetime import datetime

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
MEM_DIR = os.path.join(WORKSPACE, "memory")
INDEX_FILE = os.path.join(MEM_DIR, "MEMORY.md")


def today_file():
    return os.path.join(MEM_DIR, f"MEMORY-{datetime.now().strftime('%Y-%m-%d')}.md")


def _ensure_mem_dir():
    os.makedirs(MEM_DIR, exist_ok=True)


def _day_header():
    now = datetime.now()
    return f"# {now.strftime('%Y-%m-%d')} · {now.strftime('%A').lower()}\n"


def write_memory(text, source="conversation"):
    """append one observation to today's memory file, under its source marker."""
    _ensure_mem_dir()
    path = today_file()
    text = text.strip().rstrip("\n")
    if not text:
        return path

    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(_day_header() + "\n")

    # put the observation under the right marker
    with open(path) as f:
        content = f.read()

    if source == "heartbeat":
        marker = "\n## heartbeat\n\n"
        if marker not in content:
            content += marker
        with open(path, "w") as f:
            f.write(content + f"- {datetime.now().strftime('%H:%M')} · {text}\n")
    else:
        # conversation observations go at the top, before any heartbeat block
        hb = content.find("\n## heartbeat")
        if hb == -1:
            hb = len(content)
        obs = f"- {text}\n\n"
        content = content[:hb] + obs + content[hb:]
        with open(path, "w") as f:
            f.write(content)
    return path


def read_recent(days=3):
    """read the last few daily memory files, oldest first."""
    _ensure_mem_dir()
    files = sorted(
        f for f in os.listdir(MEM_DIR)
        if f.startswith("MEMORY-") and f.endswith(".md") and f != "MEMORY.md"
    )
    out = []
    for f in files[-days:]:
        with open(os.path.join(MEM_DIR, f)) as fh:
            out.append(fh.read().strip())
    return out


def read_index():
    if not os.path.exists(INDEX_FILE):
        return ""
    with open(INDEX_FILE) as f:
        return f.read().strip()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(write_memory(" ".join(sys.argv[1:]), "conversation"))
    else:
        print(read_index())
