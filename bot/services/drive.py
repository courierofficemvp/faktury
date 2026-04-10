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
        print("DRIVE: upload start")
        print("DRIVE: file_path =", file_path)
        print("DRIVE: filename =", filename)
        print("DRIVE: folder_id =", self.folder_id)

        if not self.folder_id:
            raise ValueError("GOOGLE_DRIVE_FOLDER_ID is empty")

        service = self._get_service()

        file_metadata = {
            "name": filename,
            "parents": [self.folder_id]
        }

        media = MediaFileUpload(file_path, resumable=True)

        created = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, webViewLink, name"
        ).execute()

        print("DRIVE: upload success =", created)

        link = created.get("webViewLink") or f"https://drive.google.com/file/d/{created['id']}/view"
        return link, created.get("name", filename)
