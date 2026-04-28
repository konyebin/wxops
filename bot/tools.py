"""
tools.py — Claude tool definitions and their Python implementations.

Two tools:
  1. fetch_webex_report  — calls the Webex Reports API, returns a JSON summary
  2. read_csv            — parses an in-memory CSV (uploaded via Webex), returns JSON summary
"""

import io
import json
import sys
from pathlib import Path

import pandas as pd

# Add project root to path so we can import fetch_webex_report
sys.path.insert(0, str(Path(__file__).parent.parent))
from fetch_webex_report import fetch_webex_report as _fetch_report, load_token


# ── Tool schemas (passed to Claude) ──────────────────────────────────────────

TOOL_SCHEMAS: list[dict] = [
    {
        "name": "fetch_webex_report",
        "description": (
            "Fetch a Webex usage report for a given Org ID via the Webex Reports API. "
            "Use this to get calling detail records (CDR), call queue stats, phone number "
            "inventory, auto attendant stats, hunt group stats, and more. "
            "Returns a JSON summary with row count, column list, and the first 20 rows."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "org_id": {
                    "type": "string",
                    "description": "The Webex Org ID to query (base64-encoded UUID).",
                },
                "report_type": {
                    "type": "string",
                    "enum": [
                        "cdr",
                        "call_queue",
                        "call_queue_agents",
                        "aa_summary",
                        "aa_bh",
                        "aa_ah",
                        "hunt_group",
                        "hunt_group_agents",
                        "phone_numbers",
                    ],
                    "description": (
                        "Report type to fetch. "
                        "'cdr' = Calling Detailed Call History (most comprehensive). "
                        "'phone_numbers' = Telephone Number inventory snapshot (no date range needed). "
                        "'call_queue' / 'call_queue_agents' = Call Queue stats. "
                        "'aa_summary' / 'aa_bh' / 'aa_ah' = Auto Attendant stats. "
                        "'hunt_group' / 'hunt_group_agents' = Hunt Group stats."
                    ),
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format. Defaults to 30 days ago.",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format. Defaults to today.",
                },
            },
            "required": ["org_id", "report_type"],
        },
    },
    {
        "name": "read_csv",
        "description": (
            "Parse and analyse a CSV file that was uploaded to this chat. "
            "Returns column names, row count, data types, numeric summaries, and the first 20 rows. "
            "For CDR files it also returns Cisco Calling Plan–specific metrics (total minutes, "
            "unique users, call direction breakdown)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "description": "The internal file_id assigned when the CSV was uploaded.",
                },
            },
            "required": ["file_id"],
        },
    },
]


# ── Uploaded-file registry ────────────────────────────────────────────────────
# Maps file_id → raw CSV text. Populated by webex_bot.py when a file arrives.

_uploaded_files: dict[str, str] = {}


def register_uploaded_file(file_id: str, csv_text: str) -> None:
    """Store a downloaded CSV so read_csv can access it later."""
    _uploaded_files[file_id] = csv_text


# ── Tool implementations ──────────────────────────────────────────────────────

def _run_fetch_webex_report(
    org_id: str,
    report_type: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """Call the Webex Reports API and return a JSON string summary."""
    try:
        token = load_token()
    except (FileNotFoundError, ValueError) as e:
        return json.dumps({"error": f"Auth error: {e}. Run 'wxcli configure' to refresh token."})

    try:
        df = _fetch_report(
            org_id=org_id,
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            token=token,
            verbose=False,
        )
    except Exception as e:
        return json.dumps({"error": str(e)})

    return _summarise_dataframe(df, source=f"Webex {report_type} report")


def _run_read_csv(file_id: str) -> str:
    """Parse a previously uploaded CSV and return a JSON string summary."""
    csv_text = _uploaded_files.get(file_id)
    if csv_text is None:
        return json.dumps({"error": f"No uploaded file found with id '{file_id}'."})

    try:
        df = pd.read_csv(io.StringIO(csv_text), low_memory=False)
        df.columns = df.columns.str.strip()
    except Exception as e:
        return json.dumps({"error": f"Failed to parse CSV: {e}"})

    return _summarise_dataframe(df, source="uploaded CSV")


def _summarise_dataframe(df: pd.DataFrame, source: str) -> str:
    """Turn a DataFrame into a compact JSON summary for Claude."""
    summary: dict = {
        "source": source,
        "rows": len(df),
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "sample_rows": df.head(20).fillna("").to_dict(orient="records"),
    }

    # Numeric summary for any float/int columns
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        desc = df[numeric_cols].describe().round(2)
        summary["numeric_summary"] = desc.to_dict()

    # Cisco Calling Plan–specific metrics (CDR files)
    if "PSTN vendor name" in df.columns:
        ccp = df[
            df["PSTN vendor name"].astype(str).str.contains(
                "Cisco Calling Plans", case=False, na=False
            )
        ].copy()
        if not ccp.empty and "Duration" in ccp.columns:
            ccp["Duration"] = pd.to_numeric(ccp["Duration"], errors="coerce").fillna(0)
            ccp_minutes = ccp["Duration"].sum() / 60
            summary["cisco_calling_plan"] = {
                "total_ccp_calls": len(ccp),
                "total_ccp_minutes": round(ccp_minutes, 2),
                "unique_users": ccp["User"].nunique() if "User" in ccp.columns else None,
            }
            if "Direction" in ccp.columns:
                summary["cisco_calling_plan"]["direction_breakdown"] = (
                    ccp["Direction"].value_counts().to_dict()
                )
            if "User type" in ccp.columns:
                summary["cisco_calling_plan"]["user_type_breakdown"] = (
                    ccp["User type"].value_counts().to_dict()
                )

    return json.dumps(summary, default=str)


# ── Dispatcher ────────────────────────────────────────────────────────────────

def execute_tool(name: str, tool_input: dict) -> str:
    """Dispatch a Claude tool_use block to the correct implementation."""
    if name == "fetch_webex_report":
        return _run_fetch_webex_report(
            org_id=tool_input["org_id"],
            report_type=tool_input["report_type"],
            start_date=tool_input.get("start_date"),
            end_date=tool_input.get("end_date"),
        )
    elif name == "read_csv":
        return _run_read_csv(file_id=tool_input["file_id"])
    else:
        return json.dumps({"error": f"Unknown tool: {name}"})
