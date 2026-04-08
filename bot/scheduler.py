from __future__ import annotations

import logging
from datetime import date

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.config import settings
from bot.services.sheets import SheetsService

logger = logging.getLogger(__name__)


class ReminderScheduler:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.sheets = SheetsService()
        self.scheduler = AsyncIOScheduler(timezone=settings.timezone)

    async def send_deadline_reminders(self) -> None:
        today = date.today()
        invoices = self.sheets.get_due_reminders(days_threshold=7)
        for invoice in invoices:
            days_left = (invoice.deadline_date - today).days
            if days_left < 0:
                days_text = f'срок уже прошёл {abs(days_left)} дн. назад'
            elif days_left == 0:
                days_text = 'срок сегодня'
            else:
                days_text = f'осталось {days_left} дн.'

            text = (
                '⏰ Напоминание по фактуре\n\n'
                f'Дата: {invoice.invoice_date}\n'
                f'Brutto: {invoice.brutto:.2f} zł\n'
                f'К возврату: {invoice.refund:.2f} zł\n'
                f'Дедлайн: {invoice.deadline}\n'
                f'{days_text}\n\n'
                'Фактура ещё не рассчитана.'
            )
            try:
                await self.bot.send_message(chat_id=int(invoice.telegram_id), text=text)
                self.sheets.mark_reminder_sent(invoice.row_number)
            except Exception as exc:
                logger.exception('Failed to send reminder for row %s: %s', invoice.row_number, exc)

    def start(self) -> None:
        minute, hour, day, month, dow = settings.reminder_check_cron.split()
        trigger = CronTrigger(minute=minute, hour=hour, day=day, month=month, day_of_week=dow)
        self.scheduler.add_job(self.send_deadline_reminders, trigger=trigger, id='invoice_reminders', replace_existing=True)
        self.scheduler.start()
