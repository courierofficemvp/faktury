from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


@dataclass(frozen=True)
class Settings:
    bot_token: str
    google_credentials_file: str
    google_sheet_id: str
    google_worksheet_name: str
    google_drive_folder_id: str
    timezone: str
    reminder_check_cron: str


settings = Settings(
    bot_token=os.getenv('BOT_TOKEN', '').strip(),
    google_credentials_file=os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json').strip(),
    google_sheet_id=os.getenv('GOOGLE_SHEET_ID', '').strip(),
    google_worksheet_name=os.getenv('GOOGLE_WORKSHEET_NAME', 'Invoices').strip(),
    google_drive_folder_id=os.getenv('GOOGLE_DRIVE_FOLDER_ID', '').strip(),
    timezone=os.getenv('TIMEZONE', 'Europe/Warsaw').strip(),
    reminder_check_cron=os.getenv('REMINDER_CHECK_CRON', '0 9 * * *').strip(),
)


def validate_settings() -> None:
    missing = []
    if not settings.bot_token:
        missing.append('BOT_TOKEN')
    if not settings.google_sheet_id:
        missing.append('GOOGLE_SHEET_ID')
    if not settings.google_drive_folder_id:
        missing.append('GOOGLE_DRIVE_FOLDER_ID')
    if not settings.google_credentials_file:
        missing.append('GOOGLE_CREDENTIALS_FILE')

    credentials_path = BASE_DIR / settings.google_credentials_file
    if not credentials_path.exists():
        missing.append(f'credentials file not found: {credentials_path}')

    if missing:
        raise RuntimeError(
            'Missing configuration: ' + ', '.join(missing) +
            '. Fill .env and put credentials.json in the project root.'
        )
