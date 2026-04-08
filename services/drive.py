from __future__ import annotations

import mimetypes
from pathlib import Path

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from bot.config import BASE_DIR, settings

SCOPES = ['https://www.googleapis.com/auth/drive']


class DriveService:
    def __init__(self) -> None:
        credentials_path = BASE_DIR / settings.google_credentials_file
        creds = Credentials.from_service_account_file(str(credentials_path), scopes=SCOPES)
        self.service = build('drive', 'v3', credentials=creds, cache_discovery=False)

    def upload_file(self, file_path: Path, target_name: str) -> tuple[str, str]:
        mime_type = mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream'
        metadata = {
            'name': target_name,
            'parents': [settings.google_drive_folder_id],
        }
        media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=False)
        uploaded = self.service.files().create(
            body=metadata,
            media_body=media,
            fields='id, webViewLink, name',
            supportsAllDrives=True,
        ).execute()

        self.service.permissions().create(
            fileId=uploaded['id'],
            body={'type': 'anyone', 'role': 'reader'},
            fields='id',
            supportsAllDrives=True,
        ).execute()

        return uploaded['webViewLink'], uploaded['name']
