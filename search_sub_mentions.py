#!/usr/bin/env python3
"""Search 1:1 Webex messages for Sub+numbers mentions in the past year.

Usage:
    python3 search_sub_mentions.py              # print results
    python3 search_sub_mentions.py --csv        # also save to sub_mentions.csv
    python3 search_sub_mentions.py --to-me      # only messages sent TO you
    python3 search_sub_mentions.py --csv --to-me
"""

import csv
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from wxc_sdk import WebexSimpleApi


def load_token():
    config_path = Path.home() / ".wxcli" / "config.json"
    with open(config_path) as f:
        config = json.load(f)
    return config["profiles"]["default"]["token"]


def ask_org_id():
    print("\nEnter the Org ID to search (or press Enter to use your own org): ", end="", flush=True)
    org_id = input().strip()
    return org_id if org_id else None


def main():
    args = sys.argv[1:]
    export_csv = "--csv" in args
    to_me_only = "--to-me" in args

    token = load_token()

    org_id = ask_org_id()

    if org_id:
        api = WebexSimpleApi(tokens=token, org_id=org_id)
        print(f"Targeting Org ID: {org_id}", flush=True)
    else:
        api = WebexSimpleApi(tokens=token)

    # Get current user's email to filter messages sent TO them
    me = api.people.me()
    my_email = me.emails[0] if me.emails else None

    pattern = re.compile(r'\bSub\d+\b', re.IGNORECASE)
    one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)

    print(f"Signed in as: {my_email}", flush=True)
    print("Fetching all 1:1 rooms...", flush=True)
    direct_rooms = list(api.rooms.list(type="direct"))
    print(f"Found {len(direct_rooms)} direct conversations. Searching messages...\n", flush=True)

    results = []

    for i, room in enumerate(direct_rooms, 1):
        room_title = room.title or "Unknown"
        print(f"  [{i}/{len(direct_rooms)}] {room_title[:50]:<50}", end="\r", flush=True)

        try:
            for msg in api.messages.list(room_id=room.id):
                if msg.created and msg.created < one_year_ago:
                    break  # Messages are newest-first; stop when past 1 year
                sender = msg.person_email or ""
                if to_me_only and sender.lower() == (my_email or "").lower():
                    continue  # Skip messages sent by me
                text = msg.text or ""
                html = msg.html or ""
                content = text or html
                if pattern.search(content):
                    matches = pattern.findall(content)
                    results.append({
                        "date": msg.created.strftime("%Y-%m-%d %H:%M") if msg.created else "unknown",
                        "conversation_with": room_title,
                        "sender": sender,
                        "sub_ids": ", ".join(sorted(set(m.upper() for m in matches))),
                        "message": text[:500].replace("\n", " "),
                    })
        except Exception:
            continue

    print(" " * 70)  # clear progress line

    if not results:
        print("No messages found matching Sub+numbers pattern in the past year.")
        return

    results.sort(key=lambda x: x["date"])

    label = "sent to you" if to_me_only else "total"
    print(f"\nFound {len(results)} matching message(s) ({label}):\n")
    print("=" * 70)
    for r in results:
        print(f"Date:    {r['date']}")
        print(f"With:    {r['conversation_with']}")
        print(f"From:    {r['sender']}")
        print(f"Sub IDs: {r['sub_ids']}")
        print(f"Message: {r['message']}")
        print("-" * 70)

    if export_csv:
        csv_path = Path.home() / "wxops" / "sub_mentions.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["date", "conversation_with", "sender", "sub_ids", "message"])
            writer.writeheader()
            writer.writerows(results)
        print(f"\nCSV saved to: {csv_path}")


if __name__ == "__main__":
    main()
