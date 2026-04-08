from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
import os

class DriveService:
    def __init__(self):
        creds = Credentials.from_authorized_user_file('token.json')
        self.service = build('drive', 'v3', credentials=creds)

    def upload_file(self, file_path, filename):
        file_metadata = {
            'name': filename,
            'parents': [os.getenv("GOOGLE_DRIVE_FOLDER_ID")]
        }

        media = MediaFileUpload(file_path, resumable=True)

        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        return file.get('webViewLink'), filename
