from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from decimal import Decimal
from datetime import datetime
import os


STATUS_NEW = "NEW"
STATUS_CALCULATED = "CALCULATED"


def _safe(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def _to_float(value):
    try:
        if isinstance(value, str):
            value = value.replace(",", ".").strip()
        return float(value)
    except Exception:
        return 0.0


class SheetsService:
    def __init__(self):
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID")

    def _get_service(self):
        if not self.sheet_id:
            raise ValueError("GOOGLE_SHEET_ID is empty")

        creds = Credentials.from_service_account_file(
            "credentials.json",
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        return build("sheets", "v4", credentials=creds)

    def add_invoice(self, **kwargs):
        print("SHEETS: add_invoice start")
        print("SHEETS: kwargs =", kwargs)

        service = self._get_service()

        row = [[
            _safe(kwargs.get("invoice_date") or kwargs.get("date")),
            _safe(kwargs.get("brutto")),
            _safe(kwargs.get("vat")),
            _safe(kwargs.get("refund")),
            kwargs.get("status") or STATUS_NEW,
            _safe(kwargs.get("link")),
            _safe(kwargs.get("deadline")),
            _safe(kwargs.get("telegram_id")),
            _safe(kwargs.get("username")),
        ]]

        body = {"values": row}

        result = service.spreadsheets().values().append(
            spreadsheetId=self.sheet_id,
            range="Invoices!A:I",
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()

        print("SHEETS: add_invoice success =", result)
        return result

    def get_all(self):
        service = self._get_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=self.sheet_id,
            range="Invoices!A:I"
        ).execute()
        return result.get("values", [])

    def get_total_refund_for_user(self, user_id: int):
        rows = self.get_all()
        total = 0.0

        for row in rows[1:]:
            try:
                row_user_id = str(row[7]) if len(row) > 7 else ""
                status = row[4] if len(row) > 4 else ""
                refund = _to_float(row[3]) if len(row) > 3 else 0.0

                if row_user_id == str(user_id) and (status == "" or status == STATUS_NEW):
                    total += refund
            except Exception:
                continue

        return round(total, 2)

    def get_user_invoices(self, user_id: int, only_unprocessed: bool = False):
        rows = self.get_all()
        result = []

        for row in rows[1:]:
            try:
                row_user_id = str(row[7]) if len(row) > 7 else ""
                status = row[4] if len(row) > 4 else ""

                if row_user_id != str(user_id):
                    continue

                if only_unprocessed and not (status == "" or status == STATUS_NEW):
                    continue

                result.append(row)
            except Exception:
                continue

        return result

    def mark_user_invoices_calculated(self, user_id: int):
        service = self._get_service()
        rows = self.get_all()
        updated = 0

        for i, row in enumerate(rows[1:], start=2):
            try:
                row_user_id = str(row[7]) if len(row) > 7 else ""
                status = row[4] if len(row) > 4 else ""

                if row_user_id == str(user_id) and (status == "" or status == STATUS_NEW):
                    service.spreadsheets().values().update(
                        spreadsheetId=self.sheet_id,
                        range=f"Invoices!E{i}",
                        valueInputOption="USER_ENTERED",
                        body={"values": [[STATUS_CALCULATED]]}
                    ).execute()
                    updated += 1
            except Exception:
                continue

        return updated

    def get_due_reminders(self, days_threshold: int = 7):
        rows = self.get_all()
        reminders = []
        today = datetime.today().date()

        for row in rows[1:]:
            try:
                status = row[4] if len(row) > 4 else ""
                deadline_raw = row[6] if len(row) > 6 else ""
                telegram_id = row[7] if len(row) > 7 else ""

                if status not in ("", STATUS_NEW):
                    continue

                if not deadline_raw or not telegram_id:
                    continue

                deadline = datetime.strptime(deadline_raw, "%d.%m.%Y").date()
                days_left = (deadline - today).days

                if days_left <= days_threshold:
                    reminders.append({
                        "telegram_id": telegram_id,
                        "deadline": deadline_raw,
                        "days_left": days_left,
                        "row": row,
                    })
            except Exception:
                continue

        return reminders
