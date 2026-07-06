#!/usr/bin/env python3
"""
Google Sheets OAuth2 Authentication Script
Authenticates using OAuth2 client credentials and saves the token for reuse.
"""

import json
import os

CREDS_PATH = os.path.expanduser("~/knowledge-base/config/google-credentials.json")
TOKEN_PATH = os.path.expanduser("~/knowledge-base/config/google-token.json")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def authenticate():
    from google_auth_oauthlib.flow import Flow
    from google.oauth2.credentials import Credentials

    creds = None

    # Check for existing token
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # If no valid creds, run the OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
        else:
            # Manual copy-paste flow (works on Termux without a browser)
            flow = Flow.from_client_secrets_file(
                CREDS_PATH,
                scopes=SCOPES,
                redirect_uri="urn:ietf:wg:oauth:2.0:oob",
            )
            auth_url, _ = flow.authorization_url(prompt="consent")

            print("📋 Open this URL in your browser:\n")
            print(auth_url)
            print("\nAfter authorizing, paste the code below:\n")
            code = input("Enter code: ").strip()

            flow.fetch_token(code=code)
            creds = flow.credentials

        # Save token for future use
        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())
        print(f"\n✅ Token saved to {TOKEN_PATH}")

    return creds


def test_connection(creds):
    import gspread

    gc = gspread.authorize(creds)
    print("✅ Google Sheets connected successfully!")
    print("\n📋 Your accessible spreadsheets:")
    for sheet in gc.openall()[:10]:
        print(f"  • {sheet.title}")
    return gc


if __name__ == "__main__":
    print("🔐 Starting Google Sheets authentication...")
    print("   This will open a URL — copy/paste it into your browser,")
    print("   authorize access, then paste the code back here.\n")
    creds = authenticate()
    test_connection(creds)
