from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import os
from decimal import Decimal

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

STATUS_NEW = "NEW"
STATUS_CALCULATED = "CALCULATED"

def safe(value):
    if isinstance(value, Decimal):
        return float(value)
    return value

def to_float(val):
    try:
        if isinstance(val, str):
            val = val.replace(",", ".")
        return float(val)
    except:
        return 0

class SheetsService:
    def __init__(self):
        creds = Credentials.from_service_account_file(
            'credentials.json',
            scopes=SCOPES
        )
        self.service = build('sheets', 'v4', credentials=creds)
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID")

    def add_invoice(self, **kwargs):
        status = kwargs.get("status") or STATUS_NEW

        values = [[
            safe(kwargs.get("invoice_date") or kwargs.get("date")),
            safe(kwargs.get("brutto")),
            safe(kwargs.get("vat")),
            safe(kwargs.get("refund")),
            status,
            safe(kwargs.get("link")),
            safe(kwargs.get("deadline")),
            safe(kwargs.get("telegram_id")),
            safe(kwargs.get("username")),
        ]]

        self.service.spreadsheets().values().append(
            spreadsheetId=self.sheet_id,
            range="Invoices!A:I",
            valueInputOption="USER_ENTERED",
            body={'values': values}
        ).execute()

    def get_all(self):
        return self.service.spreadsheets().values().get(
            spreadsheetId=self.sheet_id,
            range="Invoices!A:I"
        ).execute().get('values', [])

    def get_total_refund_for_user(self, telegram_id):
        rows = self.get_all()
        total = 0

        for row in rows[1:]:
            try:
                if str(row[7]) == str(telegram_id):
                    status = row[4] if len(row) > 4 else ""
                    refund = to_float(row[3]) if len(row) > 3 else 0

                    if status == "" or status == STATUS_NEW:
                        total += refund
            except:
                continue

        return round(total, 2)

    def get_user_invoices(self, telegram_id, only_unprocessed=False):
        rows = self.get_all()
        result = []

        for row in rows[1:]:
            try:
                if str(row[7]) == str(telegram_id):
                    status = row[4] if len(row) > 4 else ""

                    if only_unprocessed and not (status == "" or status == STATUS_NEW):
                        continue

                    result.append(row)
            except:
                continue

        return result

    def mark_user_invoices_calculated(self, telegram_id):
        rows = self.get_all()
        updated = 0

        for i, row in enumerate(rows[1:], start=2):
            try:
                if str(row[7]) == str(telegram_id):
                    status = row[4] if len(row) > 4 else ""

                    if status == "" or status == STATUS_NEW:
                        self.service.spreadsheets().values().update(
                            spreadsheetId=self.sheet_id,
                            range=f"Invoices!E{i}",
                            valueInputOption="USER_ENTERED",
                            body={"values": [[STATUS_CALCULATED]]}
                        ).execute()
                        updated += 1
            except:
                continue

        return updated
