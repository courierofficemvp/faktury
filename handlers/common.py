from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
import tempfile

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dateutil.relativedelta import relativedelta

from bot.handlers.keyboards import back_menu, date_menu, invoices_menu, main_menu, refund_menu, vat_menu
from bot.handlers.states import AddInvoiceStates
from bot.services.drive import DriveService
from bot.services.sheets import SheetsService, STATUS_NEW
from bot.services.vat import calculate_vat_and_refund, to_decimal

router = Router()

sheets_service = SheetsService()
drive_service = DriveService()


def _format_money(value: Decimal) -> str:
    return f'{value:.2f} zł'


def _parse_manual_date(text: str) -> str | None:
    try:
        parsed = datetime.strptime(text.strip(), '%d.%m.%Y').date()
        return parsed.strftime('%d.%m.%Y')
    except ValueError:
        return None


def _deadline_from_date(date_str: str) -> str:
    invoice_dt = datetime.strptime(date_str, '%d.%m.%Y').date()
    deadline = invoice_dt + relativedelta(months=3)
    return deadline.strftime('%d.%m.%Y')


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        'Привет! Я бот для учёта фактур. Выбери действие в меню ниже.',
        reply_markup=main_menu(),
    )


@router.message(F.text == '⬅️ Назад')
async def universal_back(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state == AddInvoiceStates.waiting_vat.state:
        await state.set_state(AddInvoiceStates.waiting_amount)
        await message.answer('Введи сумму brutto числом. Например: 123.45', reply_markup=back_menu())
        return
    if current_state in {AddInvoiceStates.waiting_date_choice.state, AddInvoiceStates.waiting_manual_date.state}:
        await state.set_state(AddInvoiceStates.waiting_vat)
        await message.answer('Выбери ставку VAT:', reply_markup=vat_menu())
        return
    if current_state == AddInvoiceStates.waiting_file.state:
        await state.set_state(AddInvoiceStates.waiting_date_choice)
        await message.answer('Выбери дату фактуры:', reply_markup=date_menu())
        return

    await state.clear()
    await message.answer('Главное меню.', reply_markup=main_menu())


@router.message(F.text == '➕ Добавить фактуру')
async def add_invoice_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AddInvoiceStates.waiting_amount)
    await message.answer(
        'Введи сумму brutto числом. Например: 123.45',
        reply_markup=back_menu(),
    )


@router.message(AddInvoiceStates.waiting_amount)
async def process_amount(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer('Отправь сумму текстом. Например: 123.45')
        return

    try:
        brutto = to_decimal(message.text)
        if brutto <= 0:
            raise ValueError
    except Exception:
        await message.answer('Некорректная сумма. Введи число, например: 123.45')
        return

    await state.update_data(brutto=str(brutto))
    await state.set_state(AddInvoiceStates.waiting_vat)
    await message.answer('Выбери ставку VAT:', reply_markup=vat_menu())


@router.message(AddInvoiceStates.waiting_vat, F.text.in_({'23%', '8%'}))
async def process_vat(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    brutto = to_decimal(data['brutto'])
    vat_rate = message.text
    vat_value, refund_value = calculate_vat_and_refund(brutto, vat_rate)

    await state.update_data(vat_rate=vat_rate, vat_value=str(vat_value), refund_value=str(refund_value))
    await state.set_state(AddInvoiceStates.waiting_date_choice)
    await message.answer(
        f'VAT: {_format_money(vat_value)}\nК возврату: {_format_money(refund_value)}\n\nВыбери дату фактуры:',
        reply_markup=date_menu(),
    )


@router.message(AddInvoiceStates.waiting_vat)
async def process_vat_invalid(message: Message) -> None:
    await message.answer('Выбери VAT кнопкой: 23% или 8%.')


@router.message(AddInvoiceStates.waiting_date_choice, F.text == '📅 Сегодня')
async def process_today(message: Message, state: FSMContext) -> None:
    invoice_date = date.today().strftime('%d.%m.%Y')
    deadline = _deadline_from_date(invoice_date)
    await state.update_data(invoice_date=invoice_date, deadline=deadline)
    await state.set_state(AddInvoiceStates.waiting_file)
    await message.answer(
        f'Дата: {invoice_date}\nДедлайн: {deadline}\n\nТеперь отправь PDF или фото фактуры.',
        reply_markup=back_menu(),
    )


@router.message(AddInvoiceStates.waiting_date_choice, F.text == '📅 Вчера')
async def process_yesterday(message: Message, state: FSMContext) -> None:
    invoice_date = (date.today() - timedelta(days=1)).strftime('%d.%m.%Y')
    deadline = _deadline_from_date(invoice_date)
    await state.update_data(invoice_date=invoice_date, deadline=deadline)
    await state.set_state(AddInvoiceStates.waiting_file)
    await message.answer(
        f'Дата: {invoice_date}\nДедлайн: {deadline}\n\nТеперь отправь PDF или фото фактуры.',
        reply_markup=back_menu(),
    )


@router.message(AddInvoiceStates.waiting_date_choice, F.text == '✍️ Ввести вручную')
async def process_manual_date_request(message: Message, state: FSMContext) -> None:
    await state.set_state(AddInvoiceStates.waiting_manual_date)
    await message.answer('Введи дату в формате ДД.ММ.ГГГГ. Например: 08.04.2026', reply_markup=back_menu())


@router.message(AddInvoiceStates.waiting_date_choice)
async def process_date_choice_invalid(message: Message) -> None:
    await message.answer('Выбери дату кнопкой: Сегодня, Вчера или Ввести вручную.')


@router.message(AddInvoiceStates.waiting_manual_date)
async def process_manual_date(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer('Введи дату текстом в формате ДД.ММ.ГГГГ.')
        return

    invoice_date = _parse_manual_date(message.text)
    if not invoice_date:
        await message.answer('Неверный формат даты. Используй ДД.ММ.ГГГГ, например 08.04.2026')
        return

    deadline = _deadline_from_date(invoice_date)
    await state.update_data(invoice_date=invoice_date, deadline=deadline)
    await state.set_state(AddInvoiceStates.waiting_file)
    await message.answer(
        f'Дата: {invoice_date}\nДедлайн: {deadline}\n\nТеперь отправь PDF или фото фактуры.',
        reply_markup=back_menu(),
    )


async def _save_message_file(bot: Bot, message: Message) -> tuple[Path, str]:
    suffix = '.bin'
    file_name = 'invoice_file'
    tg_file = None

    if message.document:
        tg_file = await bot.get_file(message.document.file_id)
        suffix = Path(message.document.file_name or '').suffix or '.pdf'
        file_name = message.document.file_name or f'invoice{suffix}'
    elif message.photo:
        tg_file = await bot.get_file(message.photo[-1].file_id)
        suffix = '.jpg'
        file_name = f'photo_{message.photo[-1].file_unique_id}.jpg'
    else:
        raise ValueError('Unsupported file type')

    temp_dir = Path(tempfile.gettempdir())
    local_path = temp_dir / f'{message.from_user.id}_{message.message_id}{suffix}'
    await bot.download(tg_file, destination=local_path)
    return local_path, file_name


@router.message(AddInvoiceStates.waiting_file, F.document | F.photo)
async def process_file(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    local_path = None
    try:
        local_path, original_name = await _save_message_file(bot, message)
        upload_name = f"invoice_{message.from_user.id}_{data['invoice_date'].replace('.', '-')}_{original_name}"
        link, saved_name = drive_service.upload_file(local_path, upload_name)

        sheets_service.add_invoice(
            telegram_id=message.from_user.id,
            username=message.from_user.username or '',
            invoice_date=data['invoice_date'],
            brutto=to_decimal(data['brutto']),
            vat_rate=data['vat_rate'],
            vat=to_decimal(data['vat_value']),
            refund=to_decimal(data['refund_value']),
            link=link,
            deadline=data['deadline'],
            file_name=saved_name,
        )
    except Exception as exc:
        await message.answer(f'Не удалось сохранить фактуру: {exc}')
        return
    finally:
        if local_path and local_path.exists():
            local_path.unlink(missing_ok=True)

    await state.clear()
    await message.answer(
        'Фактура сохранена.\n\n'
        f"Дата: {data['invoice_date']}\n"
        f"Brutto: {_format_money(to_decimal(data['brutto']))}\n"
        f"VAT: {_format_money(to_decimal(data['vat_value']))}\n"
        f"К возврату: {_format_money(to_decimal(data['refund_value']))}\n"
        f"Дедлайн: {data['deadline']}",
        reply_markup=main_menu(),
    )


@router.message(AddInvoiceStates.waiting_file)
async def process_file_invalid(message: Message) -> None:
    await message.answer('Отправь PDF документ или фото фактуры.')


@router.message(F.text == '💰 К возврату')
async def refund_info(message: Message) -> None:
    total = sheets_service.get_total_refund_for_user(message.from_user.id)
    count = len(sheets_service.get_user_invoices(message.from_user.id, only_unprocessed=True))
    await message.answer(
        f'Нерассчитанных фактур: {count}\nК возврату: {_format_money(total)}',
        reply_markup=refund_menu(has_items=count > 0),
    )


@router.message(F.text == '✅ Рассчитать VAT')
async def calculate_all(message: Message) -> None:
    count = sheets_service.mark_user_invoices_calculated(message.from_user.id)
    await message.answer(
        f'Готово. Отмечено как рассчитанные: {count}.\nТекущая сумма к возврату: 0.00 zł',
        reply_markup=main_menu(),
    )


@router.message(F.text == '📄 Мои фактуры')
async def my_invoices_menu(message: Message) -> None:
    await message.answer('Выбери, что показать:', reply_markup=invoices_menu())


async def _send_invoices_list(message: Message, only_unprocessed: bool) -> None:
    invoices = sheets_service.get_user_invoices(message.from_user.id, only_unprocessed=only_unprocessed)
    if not invoices:
        await message.answer('Фактур не найдено.', reply_markup=invoices_menu())
        return

    chunks = []
    for idx, item in enumerate(invoices, start=1):
        chunks.append(
            f'{idx}. Дата: {item.invoice_date}\n'
            f'   Brutto: {_format_money(item.brutto)}\n'
            f'   VAT: {item.vat_rate} / {_format_money(item.vat)}\n'
            f'   К возврату: {_format_money(item.refund)}\n'
            f'   Статус: {item.status}\n'
            f'   Дедлайн: {item.deadline}\n'
            f'   Файл: {item.link}'
        )

    text = '\n\n'.join(chunks)
    while text:
        part = text[:3500]
        cut = part.rfind('\n\n')
        if len(text) > 3500 and cut > 0:
            send_part = text[:cut]
            text = text[cut + 2:]
        else:
            send_part = text
            text = ''
        await message.answer(send_part, reply_markup=invoices_menu() if not text else None)


@router.message(F.text == '📄 Нерассчитанные')
async def show_unprocessed_invoices(message: Message) -> None:
    await _send_invoices_list(message, only_unprocessed=True)


@router.message(F.text == '📚 Все')
async def show_all_invoices(message: Message) -> None:
    await _send_invoices_list(message, only_unprocessed=False)
