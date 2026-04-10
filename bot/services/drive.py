from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os


class DriveService:
    def __init__(self):
        self.folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

    def _get_service(self):
        creds = Credentials.from_service_account_file(
            "credentials.json",
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        return build("drive", "v3", credentials=creds)

    def upload_file(self, file_path: str, filename: str):
        print("UPLOAD START:", file_path, filename)
        print("FOLDER ID:", self.folder_id)
        service = self._get_service()

        file_metadata = {
            "name": filename,
            "parents": [self.folder_id]
        }

        media = MediaFileUpload(file_path, resumable=True)

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

        return file.get("id")
