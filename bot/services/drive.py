from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os


class DriveService:
    def __init__(self):
        creds = Credentials.from_service_account_file(
            "credentials.json",
            scopes=["https://www.googleapis.com/auth/drive"]
        )

        self.service = build("drive", "v3", credentials=creds)
        self.folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

    def upload_file(self, file_path: str, filename: str):
        file_metadata = {
            "name": filename,
            "parents": [self.folder_id]
        }

        media = MediaFileUpload(file_path, resumable=True)

        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

        return file.get("id")
