#!/usr/bin/env python3
"""
Helper script to generate Gmail API refresh token.

Usage:
1. Place your gmail_credentials.json in credentials/ folder
2. Run: python scripts/generate_gmail_token.py (from project root)
3. Follow the browser authentication flow
4. Copy the contents of credentials/gmail_token.json to GitHub secrets
"""

import os
import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send'
]

# Get project root (parent of scripts/ folder)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CREDENTIALS_DIR = PROJECT_ROOT / 'credentials'

def main():
    print("=" * 80)
    print("Gmail API Token Generator")
    print("=" * 80)
    print()

    credentials_file = CREDENTIALS_DIR / 'gmail_credentials.json'
    token_file = CREDENTIALS_DIR / 'gmail_token.json'

    # Check if credentials file exists
    if not credentials_file.exists():
        print(f"✗ Error: {credentials_file} not found")
        print()
        print("Please download your OAuth credentials from Google Cloud Console:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Navigate to APIs & Services > Credentials")
        print("3. Create OAuth 2.0 Client ID (Desktop app)")
        print("4. Download and save as credentials/gmail_credentials.json")
        print()
        return 1

    print(f"✓ Found {credentials_file}")
    print()
    print("Starting authentication flow...")
    print("A browser window will open. Please sign in with your Gmail account.")
    print()

    try:
        # Run OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(
            str(credentials_file), SCOPES)
        creds = flow.run_local_server(port=0)

        # Save token
        token_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }

        with open(token_file, 'w') as f:
            json.dump(token_data, f, indent=2)

        print()
        print("=" * 80)
        print("✓ Token generated successfully!")
        print("=" * 80)
        print()
        print("Next steps:")
        print(f"1. Copy the contents of {token_file}")
        print("2. Go to your GitHub repository > Settings > Secrets and variables > Actions")
        print("3. Create a new secret named GMAIL_TOKEN")
        print(f"4. Paste the entire contents of {token_file} as the value")
        print()
        print(f"Note: Keep {token_file} secure and never commit it to git!")
        print()
        
        return 0
        
    except Exception as e:
        print()
        print("=" * 80)
        print("✗ Error occurred:")
        print(str(e))
        print("=" * 80)
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
