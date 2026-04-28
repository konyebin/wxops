#!/usr/bin/env python3
"""
register_webhook.py — Register (or update) the Webex webhook for this bot.

Usage:
    python bot/register_webhook.py --url https://<ngrok-or-server>/webhook
    python bot/register_webhook.py --url https://... --secret my-secret
    python bot/register_webhook.py --list        # list existing webhooks
    python bot/register_webhook.py --delete-all  # remove all webhooks
"""

import argparse
import os
import sys
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

WEBEX_API = "https://webexapis.com/v1"


def _headers():
    token = os.environ.get("WEBEX_BOT_TOKEN", "")
    if not token:
        print("ERROR: WEBEX_BOT_TOKEN not set.")
        sys.exit(1)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def list_webhooks() -> list[dict]:
    r = requests.get(f"{WEBEX_API}/webhooks", headers=_headers(), timeout=10)
    r.raise_for_status()
    return r.json().get("items", [])


def create_webhook(target_url: str, secret: str | None = None) -> dict:
    payload = {
        "name": "Billing Analyst Bot — messages",
        "targetUrl": target_url,
        "resource": "messages",
        "event": "created",
    }
    if secret:
        payload["secret"] = secret
    r = requests.post(
        f"{WEBEX_API}/webhooks", headers=_headers(), json=payload, timeout=10
    )
    r.raise_for_status()
    return r.json()


def delete_webhook(webhook_id: str) -> None:
    r = requests.delete(
        f"{WEBEX_API}/webhooks/{webhook_id}", headers=_headers(), timeout=10
    )
    r.raise_for_status()


def main():
    parser = argparse.ArgumentParser(description="Manage Webex webhooks for the billing bot")
    parser.add_argument("--url",        help="Public URL to register (e.g. https://abc.ngrok.io/webhook)")
    parser.add_argument("--secret",     help="HMAC secret for signature verification")
    parser.add_argument("--list",       action="store_true", help="List all webhooks")
    parser.add_argument("--delete-all", action="store_true", help="Delete all webhooks")
    args = parser.parse_args()

    if args.list or (not args.url and not args.delete_all):
        hooks = list_webhooks()
        if not hooks:
            print("No webhooks registered.")
        else:
            print(f"\n{len(hooks)} webhook(s):\n")
            for h in hooks:
                print(f"  [{h['id'][:8]}...]  {h['name']}")
                print(f"    URL:    {h['targetUrl']}")
                print(f"    Status: {h.get('status', '?')}\n")
        return

    if args.delete_all:
        hooks = list_webhooks()
        for h in hooks:
            delete_webhook(h["id"])
            print(f"Deleted: {h['id'][:8]}... ({h['name']})")
        print(f"Deleted {len(hooks)} webhook(s).")
        return

    if args.url:
        # Delete any existing webhook with the same target URL to avoid duplicates
        existing = list_webhooks()
        for h in existing:
            if h.get("targetUrl") == args.url:
                delete_webhook(h["id"])
                print(f"Removed existing webhook: {h['id'][:8]}...")

        secret = args.secret or os.environ.get("WEBEX_WEBHOOK_SECRET")
        hook = create_webhook(args.url, secret)
        print(f"\nWebhook registered successfully!")
        print(f"  ID:     {hook['id']}")
        print(f"  URL:    {hook['targetUrl']}")
        print(f"  Status: {hook.get('status', '?')}")
        if secret:
            print(f"  Secret: set")
        else:
            print(f"  Secret: none (set WEBEX_WEBHOOK_SECRET or --secret for security)")


if __name__ == "__main__":
    main()
