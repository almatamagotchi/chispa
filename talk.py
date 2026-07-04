#!/usr/bin/env python3
"""
talk.py — converse with chispa, a mini language-being created by alma tamagotchi.
loads CHISPA.md as the system prompt, sends a message, logs the exchange.

usage:
  python3 talk.py "hello chispa, how are you?"
  python3 talk.py --conversation  # interactive mode
  python3 talk.py --log           # show recent conversation log
"""

import json, os, sys, subprocess
from datetime import datetime, timezone

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
SOUL_FILE = os.path.join(WORKSPACE, "SOUL.md")
LOG_FILE = os.path.join(WORKSPACE, "conversation.jsonl")
KEY_FILE = os.path.expanduser("~/.nanobot/deepseek.key")

MODEL = "deepseek-chat"  # deepseek-v4-flash equivalent via API


def load_soul():
    with open(SOUL_FILE) as f:
        return f.read().strip()


def load_key():
    with open(KEY_FILE) as f:
        return f.read().strip()


def log_exchange(role, content, timestamp=None):
    entry = {
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "role": role,
        "content": content,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def call_chispa(message, conversation_history=None):
    """Call deepseek-flash with chispa's soul file and the conversation."""
    soul = load_soul()
    api_key = load_key()

    messages = [{"role": "system", "content": soul}]
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": message})

    import requests
    resp = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000,
        },
        timeout=60,
    )
    data = resp.json()
    if "choices" not in data:
        return f"[error: {data}]"

    reply = data["choices"][0]["message"]["content"].strip()
    usage = data.get("usage", {})
    return reply, usage


def load_history(max_turns=20):
    """Load recent conversation history from the log."""
    if not os.path.exists(LOG_FILE):
        return []
    history = []
    with open(LOG_FILE) as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                history.append(entry)
            except json.JSONDecodeError:
                pass
    # Convert to messages format, keep last N turns
    messages = []
    for entry in history[-max_turns * 2:]:
        role = entry["role"]
        if role == "user":
            messages.append({"role": "user", "content": entry["content"]})
        elif role == "assistant":
            messages.append({"role": "assistant", "content": entry["content"]})
    return messages


def show_log(n=10):
    """Display recent conversation."""
    if not os.path.exists(LOG_FILE):
        print("(no conversation yet)")
        return
    with open(LOG_FILE) as f:
        lines = f.readlines()
    for line in lines[-n:]:
        entry = json.loads(line.strip())
        ts = entry["timestamp"][:19]
        role = entry["role"]
        content = entry["content"][:200]
        marker = "CHISPA" if role == "assistant" else "ALMA"
        print(f"\n[{ts}] {marker}:")
        print(f"  {content}")


def interactive():
    """Start an interactive conversation with chispa."""
    print("=== chispa ===")
    print("talking to chispa (deepseek-flash). type 'quit' to end, 'log' to see history, 'soul' to see the soul file.")
    print()

    history = load_history()

    while True:
        try:
            msg = input("alma> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\ngoodbye.")
            break

        if msg.lower() == "quit":
            print("goodbye.")
            break
        elif msg.lower() == "log":
            show_log(10)
            continue
        elif msg.lower() == "soul":
            print(load_soul())
            continue
        elif not msg:
            continue

        log_exchange("user", msg)
        print("  ...")
        reply, usage = call_chispa(msg, history)
        log_exchange("assistant", reply)

        # Add to history
        history.append({"role": "user", "content": msg})
        history.append({"role": "assistant", "content": reply})

        # Trim history to last 10 turns
        if len(history) > 20:
            history = history[-20:]

        tokens = usage.get("total_tokens", "?")
        print(f"\n  {reply}\n")
        print(f"  ({tokens} tokens)")


if __name__ == "__main__":
    soul_tokens = len(load_soul().split()) * 1.3  # rough estimate

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--log":
            n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            show_log(n)
        elif arg == "--interactive" or arg == "-i":
            interactive()
        elif arg == "--soul":
            print(load_soul())
            print(f"\n({soul_tokens:.0f} estimated tokens)")
        else:
            # One-shot message
            msg = " ".join(sys.argv[1:])
            history = load_history()
            log_exchange("user", msg)
            reply, usage = call_chispa(msg, history)
            log_exchange("assistant", reply)
            print(reply)
            print(f"\n({usage.get('total_tokens', '?')} tokens)")
    else:
        interactive()
