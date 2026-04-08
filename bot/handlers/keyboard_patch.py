from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from bot.services.sheets import SheetsService

sheets_service = SheetsService()

def get_main_keyboard(user_id):
    total = sheets_service.get_total_refund_for_user(user_id)

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить фактуру")],
            [KeyboardButton(text=f"💰 К возврату: {total} zł")],
            [KeyboardButton(text="📄 Мои фактуры")]
        ],
        resize_keyboard=True
    )
