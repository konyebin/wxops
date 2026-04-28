"""
system_prompt.py — Build the cached system prompt for the billing analyst bot.

Both MD context files are marked with cache_control so the large static text is
written to cache on the first request and read cheaply on every subsequent call.
"""

from pathlib import Path

CONTEXT_DIR = Path(__file__).parent.parent / "context"


def load_system_prompt() -> list[dict]:
    """
    Return the system prompt as a list of cached content blocks.

    Block layout (Anthropic prompt-caching prefix order):
      [0] billingcontext_data.md  — Cisco Calling Plan billing rules + SKU table
      [1] collab_reports.md       — All Webex report field definitions

    Both blocks carry cache_control so they are cached as a single prefix.
    Anything added after these blocks (e.g. a dynamic instruction block)
    will NOT be cached — keep volatile content out of the system prompt.
    """
    billing_path = CONTEXT_DIR / "billingcontext_data.md"
    reports_path = CONTEXT_DIR / "collab_reports.md"

    if not billing_path.exists():
        raise FileNotFoundError(f"Missing context file: {billing_path}")
    if not reports_path.exists():
        raise FileNotFoundError(f"Missing context file: {reports_path}")

    billing_text = billing_path.read_text(encoding="utf-8")
    reports_text = reports_path.read_text(encoding="utf-8")

    # Role instruction prepended to the first block so it's part of the cache
    role_preamble = (
        "You are an expert Webex billing analyst working inside a Cisco partner.\n"
        "Engineers will ask you to explain customer bills, fetch Webex usage reports,\n"
        "and analyse CSV exports from Webex Control Hub.\n\n"
        "Rules:\n"
        "- Always cite the relevant SKU (e.g. A-AUD-U-TN) when explaining a charge.\n"
        "- When fetching a report, confirm the org ID and date range before interpreting data.\n"
        "- Format monetary amounts in USD with two decimal places.\n"
        "- If you are unsure about a charge, say so rather than guessing.\n\n"
    )

    return [
        {
            "type": "text",
            "text": role_preamble + billing_text,
            "cache_control": {"type": "ephemeral"},
        },
        {
            "type": "text",
            "text": reports_text,
            "cache_control": {"type": "ephemeral"},
        },
    ]
