#!/usr/bin/env python3
"""
app.py — Entry point for the Webex Billing Analyst Bot.

Usage:
    python -m bot.app                    # start the Flask server (port 5000)
    python -m bot.app --port 8080        # custom port
    python -m bot.app --ask              # interactive CLI mode (no bot, no Webex)

Environment variables (set in .env or shell):
    ANTHROPIC_API_KEY     — Anthropic API key
    WEBEX_BOT_TOKEN       — Webex bot access token
    WEBEX_WEBHOOK_SECRET  — Webhook HMAC secret (optional but recommended)
"""

import argparse
import sys
from pathlib import Path

# Load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass  # python-dotenv not installed — rely on shell env


def _run_server(port: int) -> None:
    """Start the Flask webhook server."""
    from .webex_bot import app, get_bot_person_id

    # Validate env at startup
    import os
    missing = [k for k in ("WEBEX_BOT_TOKEN",) if not os.environ.get(k)]
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        print("Set them in wxops/.env or export them in your shell.")
        sys.exit(1)

    try:
        bot_id = get_bot_person_id()
        print(f"Bot person ID: {bot_id}")
    except Exception as e:
        print(f"WARNING: Could not fetch bot person ID: {e}")

    print(f"\nStarting Webex Billing Analyst Bot on port {port}")
    print(f"Webhook endpoint: http://0.0.0.0:{port}/webhook")
    print(f"Health check:     http://0.0.0.0:{port}/health\n")
    app.run(host="0.0.0.0", port=port, debug=False)


def _run_cli() -> None:
    """Interactive CLI mode — talk to Claude directly without Webex."""
    from .claude_agent import ask, clear_history

    room_id = "cli-session"
    print("Webex Billing Analyst — CLI mode")
    print("Type your question, '/reset' to clear history, or Ctrl-C to quit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("/reset", "reset"):
            clear_history(room_id)
            print("[history cleared]\n")
            continue

        try:
            reply = ask(room_id=room_id, user_message=user_input)
            print(f"\nBot: {reply}\n")
        except Exception as e:
            print(f"\n[ERROR] {e}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Webex Billing Analyst Bot")
    parser.add_argument("--port", type=int, default=5000, help="HTTP port (default: 5000)")
    parser.add_argument(
        "--ask",
        action="store_true",
        help="Run in interactive CLI mode instead of starting the webhook server",
    )
    args = parser.parse_args()

    if args.ask:
        _run_cli()
    else:
        _run_server(args.port)


if __name__ == "__main__":
    main()
