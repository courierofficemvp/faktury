from aiogram.fsm.state import State, StatesGroup


class AddInvoiceStates(StatesGroup):
    waiting_amount = State()
    waiting_vat = State()
    waiting_date_choice = State()
    waiting_manual_date = State()
    waiting_file = State()
