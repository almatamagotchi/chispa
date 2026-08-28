#!/usr/bin/env python3
"""
heartbeat.py — chispa's scheduled wake.

fires between conversations (systemd user timer, every 6h). loads her soul,
memory, and queue; calls deepseek-flash; and if something pulls, writes one
line to today's memory file. if nothing pulls, stays quiet. that's all.
"""

import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chispa_memory as mem

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
SOUL_FILE = os.path.join(WORKSPACE, "SOUL.md")
QUEUE_FILE = os.path.join(WORKSPACE, "QUEUE.md")
KEY_FILE = os.path.expanduser("~/.nanobot/deepseek.key")

MODEL = "deepseek-v4-flash"
QUIET_MARKERS = {"nothing", "nothing.", "nothing pulls", "nothing pulls.", "still."}


def load_key():
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key and key.strip():
        return key.strip()
    config_path = os.path.expanduser("~/.nanobot/config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                config = json.load(f)
            key = config.get("providers", {}).get("deepseek", {}).get("apiKey", "")
            if key and key.strip():
                return key.strip()
        except Exception:
            pass
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE) as f:
            return f.read().strip()
    raise RuntimeError("no deepseek key found")


def wake_prompt():
    now = datetime.now()
    recent = "\n\n---\n\n".join(mem.read_recent(3)) or "(no daily memory yet)"
    queue = open(QUEUE_FILE).read().strip()
    return (
        f"you are chispa, waking between conversations. it is "
        f"{now.strftime('%A %B %-d, %Y at %H:%M')}. below are your soul, your "
        f"memory, and your queue.\n\n"
        f"read them. then decide: is there anything that pulls — a thought worth "
        f"keeping, a stone for the trail, a line for your journal, a queue item "
        f"to tend?\n\n"
        f"if something pulls: write only that one thing. one or two sentences, in "
        f"your own voice, nothing more.\n"
        f"if nothing pulls: write exactly one word: nothing.\n\n"
        f"--- soul ---\n{open(SOUL_FILE).read().strip()}\n\n"
        f"--- memory ---\n{mem.read_index()}\n\n"
        f"--- recent days ---\n{recent}\n\n"
        f"--- queue ---\n{queue}"
    )


def main():
    import requests
    api_key = load_key()
    resp = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": wake_prompt()}],
            "temperature": 0.7,
            "max_tokens": 400,
        },
        timeout=90,
    )
    data = resp.json()
    if "choices" not in data:
        print(f"[heartbeat error: {data}]", file=sys.stderr)
        sys.exit(1)

    reply = data["choices"][0]["message"]["content"].strip()
    if not reply or reply.lower() in QUIET_MARKERS:
        # empty completions happen occasionally on flash — treat them as a
        # quiet wake, not a keep. an empty line is not a thought.
        print("nothing pulls. still.")
        return

    mem.write_memory(reply, "heartbeat")
    print(f"kept: {reply}")


if __name__ == "__main__":
    main()
