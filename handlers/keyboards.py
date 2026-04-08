from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def make_keyboard(rows: list[list[str]], resize: bool = True) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=text) for text in row] for row in rows],
        resize_keyboard=resize,
    )


def main_menu() -> ReplyKeyboardMarkup:
    return make_keyboard([
        ['➕ Добавить фактуру'],
        ['💰 К возврату'],
        ['📄 Мои фактуры'],
    ])


def back_menu() -> ReplyKeyboardMarkup:
    return make_keyboard([['⬅️ Назад']])


def vat_menu() -> ReplyKeyboardMarkup:
    return make_keyboard([
        ['23%', '8%'],
        ['⬅️ Назад'],
    ])


def date_menu() -> ReplyKeyboardMarkup:
    return make_keyboard([
        ['📅 Сегодня', '📅 Вчера'],
        ['✍️ Ввести вручную'],
        ['⬅️ Назад'],
    ])


def refund_menu(has_items: bool) -> ReplyKeyboardMarkup:
    rows = []
    if has_items:
        rows.append(['✅ Рассчитать VAT'])
    rows.append(['⬅️ Назад'])
    return make_keyboard(rows)


def invoices_menu() -> ReplyKeyboardMarkup:
    return make_keyboard([
        ['📄 Нерассчитанные', '📚 Все'],
        ['⬅️ Назад'],
    ])
