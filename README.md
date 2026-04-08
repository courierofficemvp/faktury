# Telegram bot для учёта фактур

Готовый проект на **Python + aiogram 3**.

## Что умеет бот

- работает через **ReplyKeyboard**
- добавляет фактуры пошагово через FSM
- считает VAT и сумму к возврату
- сохраняет файлы фактур в **Google Drive**
- сохраняет данные в **Google Sheets**
- показывает:
  - сумму к возврату
  - список всех фактур
  - список нерассчитанных фактур
- отправляет напоминания, если до дедлайна осталось 7 дней или меньше

## Структура проекта

```text
bot_project/
├── .env.example
├── README.md
├── requirements.txt
└── bot/
    ├── __init__.py
    ├── bot.py
    ├── config.py
    ├── scheduler.py
    ├── handlers/
    │   ├── __init__.py
    │   ├── common.py
    │   ├── keyboards.py
    │   └── states.py
    └── services/
        ├── __init__.py
        ├── drive.py
        ├── sheets.py
        └── vat.py
```

## Формулы

- **23%**: `VAT = brutto * 23 / 123`, `возврат = VAT / 2`
- **8%**: `VAT = brutto * 8 / 108`, `возврат = VAT / 2`
- **Дедлайн**: `дата фактуры + 3 месяца`

## Колонки в Google Sheets

При первом запуске бот создаёт или обновляет заголовки:

- Telegram ID
- Username
- Created At
- Date
- Brutto
- VAT Rate
- VAT
- Refund
- Status
- Link
- Deadline
- Reminder Sent
- File Name

## Как подготовить Google Sheets

1. Создай проект в Google Cloud.
2. Включи:
   - **Google Sheets API**
   - **Google Drive API**
3. Создай **Service Account**.
4. Скачай JSON-ключ и положи его в корень проекта как `credentials.json`.
5. Создай Google Sheets таблицу.
6. Скопируй её ID из URL и вставь в `.env` в `GOOGLE_SHEET_ID`.
7. Открой таблицу и **поделись** ею с email service account-а с правами Editor.

Пример ID таблицы:

```text
https://docs.google.com/spreadsheets/d/1AbCDefGhIjKlMnOpQrStUvWxYz1234567890/edit#gid=0
```

ID таблицы:

```text
1AbCDefGhIjKlMnOpQrStUvWxYz1234567890
```

## Как подготовить Google Drive

1. Создай папку в Google Drive.
2. Скопируй ID папки из URL.
3. Вставь ID в `.env` в `GOOGLE_DRIVE_FOLDER_ID`.
4. Поделись этой папкой с email service account-а с правами **Editor**.

Пример:

```text
https://drive.google.com/drive/folders/1ZYXwVuTsRqPoNmLkJiHgFeDcBa987654
```

ID папки:

```text
1ZYXwVuTsRqPoNmLkJiHgFeDcBa987654
```

## Настройка Telegram

1. Создай бота через `@BotFather`.
2. Возьми токен.
3. Скопируй `.env.example` в `.env`.
4. Заполни значения.

Пример `.env`:

```env
BOT_TOKEN=123456:ABC-DEF...
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_SHEET_ID=your_google_sheet_id
GOOGLE_WORKSHEET_NAME=Invoices
GOOGLE_DRIVE_FOLDER_ID=your_google_drive_folder_id
TIMEZONE=Europe/Warsaw
REMINDER_CHECK_CRON=0 9 * * *
```

## Установка на macOS

```bash
cd bot_project
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

После этого:

- добавь `credentials.json` в корень проекта
- заполни `.env`

Запуск:

```bash
source venv/bin/activate
python -m bot.bot
```

## Логика меню

### Главное меню
- ➕ Добавить фактуру
- 💰 К возврату
- 📄 Мои фактуры

### Добавить фактуру
1. ввод суммы brutto
2. выбор VAT через кнопки
3. выбор даты:
   - Сегодня
   - Вчера
   - Ввести вручную
4. отправка PDF или фото
5. загрузка файла в Google Drive
6. запись строки в Google Sheets

### К возврату
- показывает сумму всех нерассчитанных возвратов
- кнопка **Рассчитать VAT** помечает все нерассчитанные фактуры пользователя как рассчитанные

### Мои фактуры
- **Нерассчитанные**
- **Все**

## Напоминания

Напоминания запускаются через `APScheduler` по cron из `.env`.

По умолчанию:

```text
0 9 * * *
```

Это значит: каждый день в **09:00** по времени `Europe/Warsaw`.

## Деплой на GitHub

```bash
git init
git add .
git commit -m "Initial invoice bot"
git branch -M main
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

## Деплой на Bothost

Общий сценарий:

1. Создай новый Python app.
2. Подключи GitHub-репозиторий.
3. Укажи стартовую команду:

```bash
python -m bot.bot
```

4. Добавь переменные окружения из `.env`.
5. Загрузи `credentials.json` в файловую систему сервера или добавь его вручную.
6. Убедись, что путь в `GOOGLE_CREDENTIALS_FILE` совпадает с реальным путём к JSON-файлу.

## Важные замечания

- бот использует **MemoryStorage**, поэтому FSM-состояния не сохраняются после перезапуска
- данные фактур сохраняются в Google Sheets, поэтому сами фактуры не теряются
- для работы напоминаний бот должен быть постоянно запущен
- если используешь общий Google Drive folder, бот делает загруженные файлы доступными по ссылке

## Что можно улучшить потом

- SQLite/PostgreSQL для локального кеша и логов
- удаление фактур
- редактирование фактур
- экспорт в Excel/PDF
- отдельные роли admin/user
- webhook вместо polling
