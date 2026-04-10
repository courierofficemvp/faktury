from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import os


class SheetsService:
    def __init__(self):
        creds = Credentials.from_service_account_file(
            "credentials.json",
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )

        self.service = build("sheets", "v4", credentials=creds)
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID")

    def add_invoice(self, values: list):
        print("SHEETS WRITE START")

        body = {
            "values": [values]
        }

        self.service.spreadsheets().values().append(
            spreadsheetId=self.sheet_id,
            range="A1",
            valueInputOption="RAW",
            body=body
        ).execute()

    def get_due_reminders(self, days_threshold: int = 7):
        try:
            return []
        except Exception as e:
            print(f"Error in get_due_reminders: {e}")
            return []
