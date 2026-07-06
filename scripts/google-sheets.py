#!/usr/bin/env python3
"""
Google Sheets Helper — Read, Write, Create, and Manage Google Sheets.
Uses saved OAuth2 token from google-sheets-auth.py.
"""

import json
import os
import sys

CREDS_PATH = os.path.expanduser("~/knowledge-base/config/google-credentials.json")
TOKEN_PATH = os.path.expanduser("~/knowledge-base/config/google-token.json")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_client():
    """Get authenticated gspread client."""
    import gspread
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    if not os.path.exists(TOKEN_PATH):
        print("❌ Not authenticated yet. Run google-sheets-auth.py first.")
        sys.exit(1)

    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return gspread.authorize(creds)


def list_sheets():
    """List all accessible spreadsheets."""
    gc = get_client()
    sheets = gc.openall()
    print(f"📋 Found {len(sheets)} spreadsheet(s):\n")
    for i, sheet in enumerate(sheets, 1):
        print(f"  {i}. {sheet.title}")
        print(f"     ID: {sheet.id}")
        print(f"     URL: https://docs.google.com/spreadsheets/d/{sheet.id}")
        print()


def read_sheet(spreadsheet_name_or_id, worksheet_name=None):
    """Read all data from a sheet."""
    gc = get_client()
    try:
        sh = gc.open(spreadsheet_name_or_id)
    except Exception:
        sh = gc.open_by_key(spreadsheet_name_or_id)

    ws = sh.worksheet(worksheet_name) if worksheet_name else sh.sheet1
    data = ws.get_all_records()
    print(f"📊 {sh.title} → {ws.title} ({len(data)} rows)\n")
    if data:
        headers = list(data[0].keys())
        print(" | ".join(headers))
        print("-" * (len(" | ".join(headers))))
        for row in data:
            print(" | ".join(str(v) for v in row.values()))
    return data


def write_to_sheet(spreadsheet_name_or_id, data, worksheet_name=None):
    """Write data to a sheet. data = list of lists (including header row)."""
    gc = get_client()
    try:
        sh = gc.open(spreadsheet_name_or_id)
    except Exception:
        sh = gc.open_by_key(spreadsheet_name_or_id)

    ws = sh.worksheet(worksheet_name) if worksheet_name else sh.sheet1
    ws.clear()
    ws.update(range_name="A1", values=data)
    print(f"✅ Wrote {len(data)} rows to {sh.title} → {ws.title}")


def create_sheet(title):
    """Create a new spreadsheet."""
    gc = get_client()
    sh = gc.create(title)
    print(f"✅ Created: {title}")
    print(f"   URL: https://docs.google.com/spreadsheets/d/{sh.id}")
    return sh


def append_rows(spreadsheet_name_or_id, rows, worksheet_name=None):
    """Append rows to the end of a sheet."""
    gc = get_client()
    try:
        sh = gc.open(spreadsheet_name_or_id)
    except Exception:
        sh = gc.open_by_key(spreadsheet_name_or_id)

    ws = sh.worksheet(worksheet_name) if worksheet_name else sh.sheet1
    ws.append_rows(rows)
    print(f"✅ Appended {len(rows)} rows to {sh.title} → {ws.title}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 google-sheets.py list")
        print("  python3 google-sheets.py read 'Sheet Name'")
        print("  python3 google-sheets.py read 'Sheet Name' 'Tab Name'")
        print("  python3 google-sheets.py create 'New Sheet Name'")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "list":
        list_sheets()
    elif cmd == "read" and len(sys.argv) >= 3:
        ws_name = sys.argv[3] if len(sys.argv) > 3 else None
        read_sheet(sys.argv[2], ws_name)
    elif cmd == "create" and len(sys.argv) >= 3:
        create_sheet(sys.argv[2])
    else:
        print(f"Unknown command: {cmd}")
