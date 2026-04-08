from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from bot.services.sheets import SheetsService

def get_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    sheets = SheetsService()
    total = sheets.get_total_refund_for_user(user_id)

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить фактуру")],
            [KeyboardButton(text=f"💰 К возврату: {total:.2f} zł")],
            [KeyboardButton(text="📄 Мои фактуры")],
            [KeyboardButton(text="✅ Рассчитать фактуры")],
        ],
        resize_keyboard=True
    )

def get_vat_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="23%"), KeyboardButton(text="8%")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )

def get_date_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Сегодня"), KeyboardButton(text="📅 Вчера")],
            [KeyboardButton(text="✍️ Ввести вручную")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )
