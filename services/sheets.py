from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import gspread
from google.oauth2.service_account import Credentials

from bot.config import BASE_DIR, settings
from bot.services.vat import to_decimal

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
]

HEADERS = [
    'Telegram ID',
    'Username',
    'Created At',
    'Date',
    'Brutto',
    'VAT Rate',
    'VAT',
    'Refund',
    'Status',
    'Link',
    'Deadline',
    'Reminder Sent',
    'File Name',
]

STATUS_NEW = 'Не рассчитано'
STATUS_DONE = 'Рассчитано'


@dataclass
class InvoiceRow:
    row_number: int
    telegram_id: str
    username: str
    created_at: str
    invoice_date: str
    brutto: Decimal
    vat_rate: str
    vat: Decimal
    refund: Decimal
    status: str
    link: str
    deadline: str
    reminder_sent: str
    file_name: str

    @property
    def deadline_date(self) -> date:
        return datetime.strptime(self.deadline, '%d.%m.%Y').date()


class SheetsService:
    def __init__(self) -> None:
        credentials_path = BASE_DIR / settings.google_credentials_file
        creds = Credentials.from_service_account_file(str(credentials_path), scopes=SCOPES)
        self.gc = gspread.authorize(creds)
        self.spreadsheet = self.gc.open_by_key(settings.google_sheet_id)
        self.worksheet = self._get_or_create_worksheet(settings.google_worksheet_name)
        self.ensure_headers()

    def _get_or_create_worksheet(self, title: str):
        try:
            return self.spreadsheet.worksheet(title)
        except gspread.WorksheetNotFound:
            return self.spreadsheet.add_worksheet(title=title, rows=1000, cols=20)

    def ensure_headers(self) -> None:
        first_row = self.worksheet.row_values(1)
        if first_row != HEADERS:
            self.worksheet.update('A1:M1', [HEADERS])

    def add_invoice(
        self,
        telegram_id: int,
        username: str,
        invoice_date: str,
        brutto: Decimal,
        vat_rate: str,
        vat: Decimal,
        refund: Decimal,
        link: str,
        deadline: str,
        file_name: str,
    ) -> None:
        now_str = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        self.worksheet.append_row([
            str(telegram_id),
            username or '',
            now_str,
            invoice_date,
            f'{brutto:.2f}',
            vat_rate,
            f'{vat:.2f}',
            f'{refund:.2f}',
            STATUS_NEW,
            link,
            deadline,
            'no',
            file_name,
        ], value_input_option='USER_ENTERED')

    def _rows_to_invoices(self, rows: list[list[str]]) -> list[InvoiceRow]:
        items: list[InvoiceRow] = []
        for idx, row in enumerate(rows, start=2):
            row = (row + [''] * len(HEADERS))[:len(HEADERS)]
            if not row[0]:
                continue
            try:
                items.append(InvoiceRow(
                    row_number=idx,
                    telegram_id=row[0],
                    username=row[1],
                    created_at=row[2],
                    invoice_date=row[3],
                    brutto=to_decimal(row[4] or '0'),
                    vat_rate=row[5],
                    vat=to_decimal(row[6] or '0'),
                    refund=to_decimal(row[7] or '0'),
                    status=row[8],
                    link=row[9],
                    deadline=row[10],
                    reminder_sent=row[11],
                    file_name=row[12],
                ))
            except Exception:
                continue
        return items

    def get_all_invoices(self) -> list[InvoiceRow]:
        rows = self.worksheet.get_all_values()[1:]
        return self._rows_to_invoices(rows)

    def get_user_invoices(self, telegram_id: int, only_unprocessed: bool = False) -> list[InvoiceRow]:
        invoices = [x for x in self.get_all_invoices() if x.telegram_id == str(telegram_id)]
        if only_unprocessed:
            invoices = [x for x in invoices if x.status == STATUS_NEW]
        return sorted(invoices, key=lambda x: datetime.strptime(x.invoice_date, '%d.%m.%Y'), reverse=True)

    def get_total_refund_for_user(self, telegram_id: int) -> Decimal:
        invoices = self.get_user_invoices(telegram_id, only_unprocessed=True)
        total = sum((x.refund for x in invoices), Decimal('0.00'))
        return total.quantize(Decimal('0.01'))

    def mark_user_invoices_calculated(self, telegram_id: int) -> int:
        invoices = self.get_user_invoices(telegram_id, only_unprocessed=True)
        count = 0
        for invoice in invoices:
            self.worksheet.update_cell(invoice.row_number, 9, STATUS_DONE)
            count += 1
        return count

    def get_due_reminders(self, days_threshold: int = 7) -> list[InvoiceRow]:
        today = date.today()
        items = []
        for invoice in self.get_all_invoices():
            days_left = (invoice.deadline_date - today).days
            if invoice.status == STATUS_NEW and invoice.reminder_sent.lower() != 'yes' and days_left <= days_threshold:
                items.append(invoice)
        return items

    def mark_reminder_sent(self, row_number: int) -> None:
        self.worksheet.update_cell(row_number, 12, 'yes')
