import os


def validate_settings():
    required_vars = [
        "BOT_TOKEN",
        "GOOGLE_SHEET_ID",
        "GOOGLE_DRIVE_FOLDER_ID",
        "GOOGLE_SHEETS_CREDENTIALS_JSON"
    ]

    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        raise RuntimeError(f"Missing ENV variables: {missing}")

    print("CONFIG OK")
