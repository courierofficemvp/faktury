from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import os


STATUS_NEW = "NEW"


class SheetsService:
    def __init__(self):
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID")

    def _get_service(self):
        creds = Credentials.from_service_account_file(
            "credentials.json",
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        return build("sheets", "v4", credentials=creds)

    def add_invoice(self, values: list):
        print("SHEETS WRITE START")

        service = self._get_service()

        body = {"values": [values]}

        service.spreadsheets().values().append(
            spreadsheetId=self.sheet_id,
            range="A1",
            valueInputOption="RAW",
            body=body
        ).execute()

    def get_total_refund_for_user(self, user_id: int):
        print(f"GET TOTAL REFUND FOR USER: {user_id}")
        return 0

    def get_due_reminders(self, days_threshold: int = 7):
        return []
