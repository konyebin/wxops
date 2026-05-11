#!/usr/bin/env python3
"""
fetch_webex_report — Fetch Webex usage reports for a given org.

Usage:
    python3 fetch_webex_report.py --org-id <ORG_ID> --report <REPORT_TYPE>
    python3 fetch_webex_report.py --org-id <ORG_ID> --report cdr --start 2026-03-01 --end 2026-04-01
    python3 fetch_webex_report.py --list-reports

Report types:
    cdr                  Calling Detailed Call History
    call_queue           Call Queue Stats
    call_queue_agents    Call Queue Agent Stats
    aa_summary           Auto Attendant Stats Summary
    aa_bh                Auto Attendant Business Hours Key Details
    aa_ah                Auto Attendant After Hours Key Details
    hunt_group           Hunt Group Stats
    hunt_group_agents    Hunt Group Agent Stats
    phone_numbers        Telephone Number Report
"""

import argparse
import io
import json
import sys
import time
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

# ── Config ────────────────────────────────────────────────────────────────────

WEBEX_BASE = "https://webexapis.com/v1"

# Report template name → Webex template title (matched via list)
REPORT_TYPE_MAP = {
    "cdr":               "Calling Detailed Call History",
    "call_queue":        "Call Queue Stats",
    "call_queue_agents": "Call Queue Agent Stats",
    "aa_summary":        "Auto-Attendant Stats Summary",
    "aa_bh":             "Auto-Attendant Business Hours Key Details",
    "aa_ah":             "Auto-Attendant After Hours Key Details",
    "hunt_group":        "Hunt Group Stats",
    "hunt_group_agents": "Hunt Group Agent Stats",
    "phone_numbers":     "Telephone Number",
}


# ── Auth ──────────────────────────────────────────────────────────────────────

_GITHUB_ENV = Path.home() / "Documents" / "GitHub" / ".env"


def _load_dotenv(path: Path) -> dict:
    """Minimal .env parser — returns key/value pairs, strips quotes."""
    env: dict = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        env[key.strip()] = val.strip().strip("'\"")
    return env


def _try_refresh(env: dict) -> str | None:
    """Silently attempt to refresh the OAuth token. Returns new access token or None."""
    refresh_tok = env.get("WEBEX_REFRESH_TOKEN", "")
    client_id = env.get("WEBEX_CLIENT_ID", "")
    client_secret = env.get("WEBEX_CLIENT_SECRET", "")
    if not all([refresh_tok, client_id, client_secret]):
        return None
    try:
        import requests as _requests
        resp = _requests.post(
            "https://webexapis.com/v1/access_token",
            data={
                "grant_type":    "refresh_token",
                "client_id":     client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_tok,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        if resp.status_code == 200:
            tokens = resp.json()
            # Persist new tokens back to .env
            lines = _GITHUB_ENV.read_text().splitlines()
            updated = []
            replaced = {"WEBEX_ACCESS_TOKEN": False, "WEBEX_REFRESH_TOKEN": False}
            for line in lines:
                if line.startswith("WEBEX_ACCESS_TOKEN="):
                    updated.append(f"WEBEX_ACCESS_TOKEN={tokens['access_token']}")
                    replaced["WEBEX_ACCESS_TOKEN"] = True
                elif line.startswith("WEBEX_REFRESH_TOKEN="):
                    updated.append(f"WEBEX_REFRESH_TOKEN={tokens['refresh_token']}")
                    replaced["WEBEX_REFRESH_TOKEN"] = True
                else:
                    updated.append(line)
            for key, done in replaced.items():
                if not done:
                    updated.append(f"{key}={tokens.get(key.lower(), '')}")
            _GITHUB_ENV.write_text("\n".join(updated) + "\n")
            return tokens["access_token"]
    except Exception:
        pass
    return None


def load_token() -> str:
    """
    Load a Webex access token.

    Priority:
      1. ~/Documents/GitHub/.env  WEBEX_ACCESS_TOKEN  (OAuth — long-lived, auto-refreshes)
      2. ~/.wxcli/config.json     token               (personal access token — 12hr expiry)
    """
    # 1. Try OAuth token from shared .env
    env = _load_dotenv(_GITHUB_ENV)
    access_token = env.get("WEBEX_ACCESS_TOKEN", "")
    if access_token:
        # Validate the token with a lightweight API call; refresh if stale
        try:
            import requests as _requests
            r = _requests.get(
                "https://webexapis.com/v1/people/me",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=8,
            )
            if r.status_code == 200:
                return access_token
            if r.status_code == 401:
                # Token expired — try refresh
                refreshed = _try_refresh(env)
                if refreshed:
                    return refreshed
            if r.status_code == 403:
                raise PermissionError(
                    "OAuth token lacks required scopes for Webex Calling/Reporting.\n"
                    "Re-run the OAuth flow with spark:all scope:\n"
                    "  cd ~/Documents/GitHub && python webex_oauth.py"
                )
        except Exception:
            pass  # fall through to wxcli

    # 2. Fall back to wxcli personal access token
    config_path = Path.home() / ".wxcli" / "config.json"
    if not config_path.exists():
        raise FileNotFoundError(
            "No valid token found.\n"
            "  Option A: run webex_oauth.py to set up OAuth tokens in ~/Documents/GitHub/.env\n"
            "  Option B: run wxcli configure to set a personal access token (12hr expiry)"
        )
    config = json.load(open(config_path))
    token = config["profiles"]["default"]["token"]
    expires_at = config["profiles"]["default"].get("expires_at")
    if expires_at:
        exp = datetime.fromisoformat(expires_at)
        if exp < datetime.now(timezone.utc):
            raise ValueError(
                "wxcli token expired.\n"
                "  Option A: run webex_oauth.py to set up OAuth tokens\n"
                "  Option B: run wxcli configure to refresh"
            )
    return token


def get_headers(token: str, org_id: str = None) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    if org_id:
        headers["X-Org-Id"] = org_id
    return headers


# ── Report Templates ──────────────────────────────────────────────────────────

def list_templates(token: str) -> list[dict]:
    """Return all available report templates."""
    r = requests.get(f"{WEBEX_BASE}/report/templates", headers=get_headers(token))
    r.raise_for_status()
    return r.json().get("items", [])


def find_template_id(templates: list[dict], title_keyword: str) -> int | None:
    """Find template ID by partial title match (case-insensitive)."""
    for t in templates:
        if title_keyword.lower() in t.get("title", "").lower():
            return t.get("Id") or t.get("id")
    return None


# ── Report Lifecycle ──────────────────────────────────────────────────────────

def create_report(token: str, template_id: str, start_date: str, end_date: str, org_id: str = None) -> str:
    """Create a report job and return its ID."""
    payload = {
        "templateId": template_id,
        "startDate": start_date,
        "endDate": end_date,
    }
    if org_id:
        payload["siteList"] = org_id  # org_id for org-scoped reports

    r = requests.post(
        f"{WEBEX_BASE}/reports",
        headers=get_headers(token),
        json=payload,
    )
    r.raise_for_status()
    item = r.json()["items"]
    return item.get("Id") or item.get("id")


def poll_report(token: str, report_id: str, timeout: int = 300) -> str:
    """Poll until report is done. Returns download URL."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = requests.get(f"{WEBEX_BASE}/reports/{report_id}", headers=get_headers(token))
        r.raise_for_status()
        items = r.json()["items"]
        item = items[0] if isinstance(items, list) else items
        status = item.get("status", "").lower()
        if status in ("done", "manual_processing"):
            return item["downloadURL"]
        elif status in ("failed", "error"):
            raise RuntimeError(f"Report generation failed: {item}")
        print(f"  Status: {status} — waiting...", end="\r", flush=True)
        time.sleep(5)
    raise TimeoutError(f"Report did not complete within {timeout}s")


def download_report(download_url: str, token: str) -> pd.DataFrame:
    """Download report CSV (or ZIP-wrapped CSV) and return as DataFrame.
    Polls until the file is available — no timeout."""
    while True:
        r = requests.get(download_url, headers=get_headers(token))
        if r.status_code == 403:
            print("  File not ready yet — retrying...", end="\r", flush=True)
            time.sleep(5)
            continue
        r.raise_for_status()
        if r.content[:2] == b"PK":
            with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
                csv_name = next(n for n in zf.namelist() if n.endswith(".csv"))
                with zf.open(csv_name) as f:
                    return pd.read_csv(f)
        return pd.read_csv(io.StringIO(r.text))


# ── Main fetch function ───────────────────────────────────────────────────────

def fetch_webex_report(
    org_id: str,
    report_type: str = "cdr",
    start_date: str = None,
    end_date: str = None,
    token: str = None,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Fetch a Webex usage report for the given org.

    Args:
        org_id:      Webex Org ID to query
        report_type: One of the keys in REPORT_TYPE_MAP (default: 'cdr')
        start_date:  YYYY-MM-DD (default: 30 days ago)
        end_date:    YYYY-MM-DD (default: today)
        token:       Webex access token (default: loaded from ~/.wxcli/config.json)
        verbose:     Print progress messages

    Returns:
        pandas DataFrame with report data
    """
    if token is None:
        token = load_token()

    # Default date range: last 30 days. End date must be at most yesterday UTC.
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    if end_date is None:
        end_date = yesterday
    elif end_date > yesterday:
        end_date = yesterday
    if start_date is None:
        start_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")

    if report_type not in REPORT_TYPE_MAP:
        raise ValueError(f"Unknown report type '{report_type}'. Valid types: {list(REPORT_TYPE_MAP)}")

    title_keyword = REPORT_TYPE_MAP[report_type]

    if verbose:
        print(f"Fetching report: {title_keyword}")
        print(f"Org ID:          {org_id}")
        print(f"Date range:      {start_date} → {end_date}")

    # 1. Get template ID
    if verbose:
        print("Looking up report template...", flush=True)
    templates = list_templates(token)
    template_id = find_template_id(templates, title_keyword)
    if not template_id:
        available = [t.get("title") for t in templates]
        raise LookupError(
            f"Template '{title_keyword}' not found.\nAvailable templates:\n" +
            "\n".join(f"  - {t}" for t in available)
        )
    if verbose:
        print(f"Template ID: {template_id}")

    # 2. Create report
    if verbose:
        print("Creating report job...", flush=True)
    report_id = create_report(token, template_id, start_date, end_date, org_id)
    if verbose:
        print(f"Report ID: {report_id}")

    # 3. Poll until done
    if verbose:
        print("Waiting for report to complete...", flush=True)
    download_url = poll_report(token, report_id)
    if verbose:
        print(f"\nReport ready. Downloading...")

    # 4. Download and return
    df = download_report(download_url, token)
    df.columns = df.columns.str.strip()

    if verbose:
        print(f"Done — {len(df):,} rows returned.")

    return df


# ── CLI entry point ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Fetch Webex usage reports via API")
    parser.add_argument("--org-id",      help="Webex Org ID to query")
    parser.add_argument("--report",      default="cdr", choices=list(REPORT_TYPE_MAP), help="Report type")
    parser.add_argument("--start",       help="Start date YYYY-MM-DD (default: 30 days ago)")
    parser.add_argument("--end",         help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--output",      help="Save results to CSV file path")
    parser.add_argument("--list-reports", action="store_true", help="List all available report templates and exit")
    args = parser.parse_args()

    try:
        token = load_token()
    except (FileNotFoundError, ValueError) as e:
        print(f"Auth error: {e}")
        sys.exit(1)

    if args.list_reports:
        templates = list_templates(token)
        print(f"\nAvailable report templates ({len(templates)}):\n")
        for t in sorted(templates, key=lambda x: x.get("service", "")):
            tid = t.get("Id") or t.get("id") or ""
            print(f"  [{tid!s:>4}]  {t.get('service',''):20}  {t.get('title','')}")
        return

    if not args.org_id:
        print("Error: --org-id is required. Use --list-reports to see available templates.")
        sys.exit(1)

    df = fetch_webex_report(
        org_id=args.org_id,
        report_type=args.report,
        start_date=args.start,
        end_date=args.end,
        token=token,
    )

    if args.output:
        df.to_csv(args.output, index=False)
        print(f"Saved to {args.output}")
    else:
        print(f"\n{df.to_string(max_rows=20, max_cols=8)}")


if __name__ == "__main__":
    main()
