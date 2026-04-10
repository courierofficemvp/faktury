from bot.services.sheets import SheetsService

def get_sheets():
    return SheetsService()

from __future__ import annotations

import os
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from pathlib import Path

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from bot.handlers.keyboard import get_keyboard, get_vat_keyboard, get_date_keyboard
from bot.services.sheets import SheetsService, STATUS_NEW
from bot.services.drive import DriveService


router = Router()
# sheets_service removed
drive_service = DriveService()

TMP_DIR = Path("tmp_uploads")
TMP_DIR.mkdir(exist_ok=True)


class AddInvoiceState(StatesGroup):
    waiting_brutto = State()
    waiting_vat = State()
    waiting_date_choice = State()
    waiting_manual_date = State()
    waiting_file = State()


def _to_decimal(value: str) -> Decimal:
    return Decimal(value.replace(",", ".")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_vat_and_refund(brutto: Decimal, vat_rate: str) -> tuple[Decimal, Decimal]:
    if vat_rate == "23%":
        vat = (brutto * Decimal("23") / Decimal("123")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    elif vat_rate == "8%":
        vat = (brutto * Decimal("8") / Decimal("108")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        raise ValueError("Nieprawidłowa stawka VAT")

    refund = (vat / Decimal("2")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return vat, refund


def parse_manual_date(text: str) -> datetime:
    return datetime.strptime(text.strip(), "%d.%m.%Y")


def format_invoice_row(row: list[str]) -> str:
    date = row[0] if len(row) > 0 else "-"
    brutto = row[1] if len(row) > 1 else "-"
    vat = row[2] if len(row) > 2 else "-"
    refund = row[3] if len(row) > 3 else "-"
    status = row[4] if len(row) > 4 and row[4] else STATUS_NEW
    link = row[5] if len(row) > 5 else "-"
    deadline = row[6] if len(row) > 6 else "-"

    return (
        f"📅 Дата: {date}\n"
        f"💵 Brutto: {brutto} zł\n"
        f"🧾 VAT: {vat} zł\n"
        f"💰 К возврату: {refund} zł\n"
        f"📌 Статус: {status}\n"
        f"⏳ Дедлайн: {deadline}\n"
        f"🔗 Ссылка: {link}"
    )


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Добро пожаловать 👋",
        reply_markup=get_keyboard(message.from_user.id)
    )


@router.message(F.text == "➕ Добавить фактуру")
async def add_invoice_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AddInvoiceState.waiting_brutto)
    await message.answer(
        "Введи сумму brutto, например: 123.45",
        reply_markup=get_keyboard(message.from_user.id)
    )


@router.message(AddInvoiceState.waiting_brutto)
async def process_brutto(message: Message, state: FSMContext):
    raw = (message.text or "").strip()

    try:
        brutto = _to_decimal(raw)
    except Exception:
        await message.answer("Неверная сумма. Введи число, например: 123.45")
        return

    await state.update_data(brutto=str(brutto))
    await state.set_state(AddInvoiceState.waiting_vat)

    await message.answer(
        "Выбери ставку VAT:",
        reply_markup=get_vat_keyboard()
    )


@router.message(AddInvoiceState.waiting_vat, F.text.in_(["23%", "8%"]))
async def process_vat(message: Message, state: FSMContext):
    data = await state.get_data()
    brutto = Decimal(data["brutto"])
    vat_rate = message.text

    vat, refund = calculate_vat_and_refund(brutto, vat_rate)

    await state.update_data(
        vat_rate=vat_rate,
        vat=str(vat),
        refund=str(refund)
    )
    await state.set_state(AddInvoiceState.waiting_date_choice)

    await message.answer(
        f"Brutto: {brutto} zł\nVAT: {vat} zł\nК возврату: {refund} zł\n\nВыбери дату фактуры:",
        reply_markup=get_date_keyboard()
    )


@router.message(AddInvoiceState.waiting_vat, F.text == "⬅️ Назад")
async def back_from_vat(message: Message, state: FSMContext):
    await state.set_state(AddInvoiceState.waiting_brutto)
    await message.answer(
        "Введи сумму brutto:",
        reply_markup=get_keyboard(message.from_user.id)
    )


@router.message(AddInvoiceState.waiting_date_choice, F.text == "📅 Сегодня")
async def process_today(message: Message, state: FSMContext):
    invoice_date = datetime.now()
    deadline = invoice_date + timedelta(days=90)

    await state.update_data(
        invoice_date=invoice_date.strftime("%d.%m.%Y"),
        deadline=deadline.strftime("%d.%m.%Y")
    )
    await state.set_state(AddInvoiceState.waiting_file)

    await message.answer(
        "Отправь PDF или фото фактуры.",
        reply_markup=get_keyboard(message.from_user.id)
    )


@router.message(AddInvoiceState.waiting_date_choice, F.text == "📅 Вчера")
async def process_yesterday(message: Message, state: FSMContext):
    invoice_date = datetime.now() - timedelta(days=1)
    deadline = invoice_date + timedelta(days=90)

    await state.update_data(
        invoice_date=invoice_date.strftime("%d.%m.%Y"),
        deadline=deadline.strftime("%d.%m.%Y")
    )
    await state.set_state(AddInvoiceState.waiting_file)

    await message.answer(
        "Отправь PDF или фото фактуры.",
        reply_markup=get_keyboard(message.from_user.id)
    )


@router.message(AddInvoiceState.waiting_date_choice, F.text == "✍️ Ввести вручную")
async def process_manual_date_request(message: Message, state: FSMContext):
    await state.set_state(AddInvoiceState.waiting_manual_date)
    await message.answer(
        "Введи дату в формате ДД.ММ.ГГГГ, например: 08.04.2026",
        reply_markup=get_keyboard(message.from_user.id)
    )


@router.message(AddInvoiceState.waiting_date_choice, F.text == "⬅️ Назад")
async def back_from_date_choice(message: Message, state: FSMContext):
    await state.set_state(AddInvoiceState.waiting_vat)
    await message.answer(
        "Выбери ставку VAT:",
        reply_markup=get_vat_keyboard()
    )


@router.message(AddInvoiceState.waiting_manual_date)
async def process_manual_date(message: Message, state: FSMContext):
    try:
        invoice_date = parse_manual_date(message.text or "")
    except Exception:
        await message.answer("Неверная дата. Используй формат ДД.ММ.ГГГГ")
        return

    deadline = invoice_date + timedelta(days=90)

    await state.update_data(
        invoice_date=invoice_date.strftime("%d.%m.%Y"),
        deadline=deadline.strftime("%d.%m.%Y")
    )
    await state.set_state(AddInvoiceState.waiting_file)

    await message.answer(
        "Отправь PDF или фото фактуры.",
        reply_markup=get_keyboard(message.from_user.id)
    )


@router.message(AddInvoiceState.waiting_file, F.document | F.photo)
async def process_file(message: Message, state: FSMContext):
    data = await state.get_data()

    try:
        if message.document:
            tg_file = message.document
            file_name = tg_file.file_name or f"invoice_{message.from_user.id}.pdf"
        else:
            tg_file = message.photo[-1]
            file_name = f"invoice_{message.from_user.id}_{int(datetime.now().timestamp())}.jpg"

        local_path = TMP_DIR / file_name

        await message.bot.download(
            tg_file,
            destination=local_path
        )

        upload_name = f"{message.from_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_name}"
        link, _ = drive_service.upload_file(str(local_path), upload_name)

        get_sheets().add_invoice(
            invoice_date=data.get("invoice_date"),
            brutto=data.get("brutto"),
            vat=data.get("vat"),
            refund=data.get("refund"),
            status=STATUS_NEW,
            link=link,
            deadline=data.get("deadline"),
            telegram_id=message.from_user.id,
            username=message.from_user.username or ""
        )

        try:
            local_path.unlink(missing_ok=True)
        except Exception:
            pass

        await state.clear()

        total = get_sheets().get_total_refund_for_user(message.from_user.id)

        await message.answer(
            f"Фактура сохранена ✅\n\n"
            f"Дата: {data.get('invoice_date')}\n"
            f"Brutto: {data.get('brutto')} zł\n"
            f"VAT: {data.get('vat')} zł\n"
            f"К возврату: {data.get('refund')} zł\n"
            f"Текущий баланс: {total:.2f} zł",
            reply_markup=get_keyboard(message.from_user.id)
        )

    except Exception:
        await message.answer(
            "Ошибка при сохранении фактуры. Проверь Google Sheets / Drive.",
            reply_markup=get_keyboard(message.from_user.id)
        )


@router.message(AddInvoiceState.waiting_file)
async def process_file_invalid(message: Message, state: FSMContext):
    await message.answer(
        "Отправь PDF или фото фактуры.",
        reply_markup=get_keyboard(message.from_user.id)
    )


@router.message(F.text.contains("💰"))
async def refund_info(message: Message):
    total = get_sheets().get_total_refund_for_user(message.from_user.id)
    count = len(get_sheets().get_user_invoices(message.from_user.id, only_unprocessed=True))

    await message.answer(
        f"Нерассчитанных фактур: {count}\nК возврату: {total:.2f} zł",
        reply_markup=get_keyboard(message.from_user.id)
    )


@router.message(F.text == "📄 Мои фактуры")
async def my_invoices(message: Message):
    invoices = get_sheets().get_user_invoices(message.from_user.id)

    if not invoices:
        await message.answer(
            "У тебя пока нет фактур.",
            reply_markup=get_keyboard(message.from_user.id)
        )
        return

    chunks = []
    current = []

    for idx, row in enumerate(invoices, start=1):
        current.append(f"{idx}.\n{format_invoice_row(row)}")
        if len(current) == 5:
            chunks.append("\n\n".join(current))
            current = []

    if current:
        chunks.append("\n\n".join(current))

    for chunk in chunks:
        await message.answer(
            chunk,
            reply_markup=get_keyboard(message.from_user.id)
        )


@router.message(F.text == "✅ Рассчитать фактуры")
async def calculate_all(message: Message):
    count = get_sheets().mark_user_invoices_calculated(message.from_user.id)
    total = get_sheets().get_total_refund_for_user(message.from_user.id)

    await message.answer(
        f"Рассчитано фактур: {count}\nТекущий баланс: {total:.2f} zł",
        reply_markup=get_keyboard(message.from_user.id)
    )
