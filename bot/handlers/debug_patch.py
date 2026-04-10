import traceback

async def debug_save_invoice(message, drive_service, sheets_service, file_path, filename, *args, **kwargs):
    try:
        print("STEP 1: start saving invoice")

        file_id = drive_service.upload_file(file_path, filename)
        print("STEP 2: file uploaded:", file_id)

        # ВАЖНО: тут подставь свою функцию записи
        sheets_service.add_invoice(*args, **kwargs)

        print("STEP 3: saved to sheets")

        await message.answer("✅ Фактура сохранена")

    except Exception as e:
        print("ERROR:", str(e))
        traceback.print_exc()

        await message.answer("❌ Ошибка при сохранении фактуры. Проверь Google Sheets / Drive.")
