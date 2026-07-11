import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # ---------- BOT ----------
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    BOT_USERNAME: str = os.getenv("BOT_USERNAME")

    # ---------- ADMINLAR ----------
    ADMINS: list = field(default_factory=list)

    # ---------- KANALLAR ----------
    ARCHIVE_CHANNEL_ID: int = int(os.getenv("ARCHIVE_CHANNEL_ID", 0))
    BACKUP_CHANNEL_ID: int = int(os.getenv("BACKUP_CHANNEL_ID", 0))
    MAIN_CHANNEL_ID: int = int(os.getenv("MAIN_CHANNEL_ID", 0))

    # ---------- DATABASE ----------
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", 5432))
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_NAME: str = os.getenv("DB_NAME")


    def __post_init__(self):
        admins_str = os.getenv("ADMINS", "")
        self.ADMINS = [int(admin_id) for admin_id in admins_str.split(",") if admin_id.strip()]


config = Config()