#!/usr/bin/env python3
"""
app.py — Entry point for the Webex Billing Analyst Bot.

Usage:
    python -m report_bot.app               # start the Flask webhook server (port 5000)
    python -m report_bot.app --port 8080   # custom port
    python -m report_bot.app --cli         # direct CLI: fetch reports & parse CSVs (no API key needed)

Environment variables (set in .env or shell):
    ANTHROPIC_API_KEY     — Anthropic API key (only needed for the webhook server)
    WEBEX_BOT_TOKEN       — Webex bot access token
    WEBEX_WEBHOOK_SECRET  — Webhook HMAC secret (optional but recommended)
"""

import argparse
import json
import sys
from pathlib import Path

# Load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass


def _run_server(port: int) -> None:
    """Start the Flask webhook server."""
    import os
    from .webex_bot import app, get_bot_person_id

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
    """
    Direct CLI — fetch reports and parse CSVs without Claude or an API key.

    Commands:
        fetch <org_id> <report_type> [start_date] [end_date]
        csv <path/to/file.csv>
        help
        quit
    """
    import io
    import sys
    from pathlib import Path as P
    import pandas as pd
    from .tools import execute_tool, register_uploaded_file
    import uuid

    print("Webex Report CLI — no API key required")
    print("Commands:")
    print("  fetch <org_id> <report_type> [YYYY-MM-DD start] [YYYY-MM-DD end]")
    print("  csv <path/to/file.csv>")
    print("  help | quit\n")
    print("Report types: cdr, call_queue, call_queue_agents, aa_summary,")
    print("              aa_bh, aa_ah, hunt_group, hunt_group_agents, phone_numbers\n")

    while True:
        try:
            raw = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye.")
            break

        if not raw:
            continue

        parts = raw.split()
        cmd = parts[0].lower()

        if cmd in ("quit", "exit", "q"):
            print("Bye.")
            break

        elif cmd == "help":
            print("  fetch <org_id> <report_type> [start] [end]")
            print("  csv <path/to/file.csv>")
            print("  quit")

        elif cmd == "fetch":
            if len(parts) < 3:
                print("Usage: fetch <org_id> <report_type> [start_date] [end_date]")
                continue
            tool_input = {
                "org_id": parts[1],
                "report_type": parts[2],
            }
            if len(parts) >= 4:
                tool_input["start_date"] = parts[3]
            if len(parts) >= 5:
                tool_input["end_date"] = parts[4]

            print(f"Fetching {tool_input['report_type']} report for org {tool_input['org_id']}...")
            result = execute_tool("fetch_webex_report", tool_input)
            data = json.loads(result)

            if "error" in data:
                print(f"ERROR: {data['error']}")
            else:
                print(f"\nRows:    {data['rows']:,}")
                print(f"Columns: {', '.join(data['columns'])}")
                if "cisco_calling_plan" in data:
                    ccp = data["cisco_calling_plan"]
                    print(f"\nCisco Calling Plan:")
                    print(f"  Calls:        {ccp['total_ccp_calls']:,}")
                    print(f"  Minutes:      {ccp['total_ccp_minutes']:,.1f}")
                    print(f"  Unique users: {ccp.get('unique_users', 'N/A')}")
                if data.get("sample_rows"):
                    print(f"\nFirst 5 rows:")
                    for row in data["sample_rows"][:5]:
                        print(f"  {row}")
            print()

        elif cmd == "csv":
            if len(parts) < 2:
                print("Usage: csv <path/to/file.csv>")
                continue
            csv_path = P(parts[1]).expanduser()
            if not csv_path.exists():
                print(f"File not found: {csv_path}")
                continue

            file_id = str(uuid.uuid4())
            register_uploaded_file(file_id, csv_path.read_text(encoding="utf-8", errors="replace"))
            result = execute_tool("read_csv", {"file_id": file_id})
            data = json.loads(result)

            if "error" in data:
                print(f"ERROR: {data['error']}")
            else:
                print(f"\nRows:    {data['rows']:,}")
                print(f"Columns: {', '.join(data['columns'])}")
                if "cisco_calling_plan" in data:
                    ccp = data["cisco_calling_plan"]
                    print(f"\nCisco Calling Plan:")
                    print(f"  Calls:        {ccp['total_ccp_calls']:,}")
                    print(f"  Minutes:      {ccp['total_ccp_minutes']:,.1f}")
                    print(f"  Unique users: {ccp.get('unique_users', 'N/A')}")
                    if "direction_breakdown" in ccp:
                        print(f"  Direction:    {ccp['direction_breakdown']}")
                    if "user_type_breakdown" in ccp:
                        print(f"  User types:   {ccp['user_type_breakdown']}")
            print()

        else:
            print(f"Unknown command: {cmd}. Type 'help' for usage.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Webex Billing Analyst Bot")
    parser.add_argument("--port", type=int, default=5000, help="HTTP port (default: 5000)")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Direct CLI mode: fetch reports and parse CSVs (no Anthropic API key needed)",
    )
    args = parser.parse_args()

    if args.cli:
        _run_cli()
    else:
        _run_server(args.port)


if __name__ == "__main__":
    main()
