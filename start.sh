#!/usr/bin/env bash
set -e

echo "$GOOGLE_DRIVE_TOKEN_JSON" > token.json
echo "$GOOGLE_SHEETS_CREDENTIALS_JSON" > credentials.json

pip install -r requirements.txt

python bot.py
