import os
import subprocess
from datetime import datetime

from aiogram import Bot
from aiogram.types import FSInputFile

from data.config import config

# Backup fayllari vaqtincha saqlanadigan papka
BACKUP_DIR = "backups"


def create_backup_file() -> str:
    """
    PostgreSQL bazasining to'liq zaxira nusxasini (.sql) yaratadi.

    `pg_dump` — PostgreSQL bilan birga keladigan rasmiy vosita, butun bazani
    (jadvallar, ma'lumotlar, struktura) bitta faylga saqlab beradi.

    -F c (custom format) ishlatilgan, chunki:
    - fayl hajmi kichikroq bo'ladi (siqilgan)
    - kerak bo'lganda `pg_restore` orqali tez va ishonchli tiklash mumkin

    :return: yaratilgan backup faylining lokal manzili
    """
    os.makedirs(BACKUP_DIR, exist_ok=True)

    # Fayl nomiga sana va vaqtni qo'shamiz — har kunlik backup alohida
    # nom bilan saqlanadi, bir-birini ustidan yozib yubormaydi.
    filename = f"backup_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.sql"
    filepath = os.path.join(BACKUP_DIR, filename)

    # pg_dump parolni argument sifatida qabul qilmaydi (xavfsizlik sababli),
    # shuning uchun uni PGPASSWORD muhit o'zgaruvchisi orqali uzatamiz.
    env = os.environ.copy()
    env["PGPASSWORD"] = config.DB_PASSWORD

    subprocess.run(
        [
            "pg_dump",
            "-h", config.DB_HOST,
            "-p", str(config.DB_PORT),
            "-U", config.DB_USER,
            "-F", "c",           # custom (siqilgan) format
            "-f", filepath,      # chiqish fayli manzili
            config.DB_NAME,
        ],
        env=env,
        check=True,  # xato bo'lsa, subprocess.CalledProcessError ko'tariladi
    )

    return filepath


async def send_backup_to_channel(bot: Bot) -> None:
    """
    Bazadan yangi backup yaratib, uni maxfiy backup kanaliga yuboradi.

    Nega kerak: agar ertaga serverga hujum bo'lsa yoki baza buzilib qolsa,
    shu kanaldagi eng so'nggi backup faylidan bazani qayta tiklash mumkin bo'ladi.

    Bu funksiya har kuni avtomatik ishga tushadi (scheduler.py orqali),
    lekin xohlasangiz admin buyruq bilan qo'lda ham chaqira olasiz.
    """
    filepath = None
    try:
        filepath = create_backup_file()
        file = FSInputFile(filepath)

        await bot.send_document(
            chat_id=config.BACKUP_CHANNEL_ID,
            document=file,
            caption=f"🗄 Backup — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        )

    except Exception as e:
        # Agar biror sabab bilan backup ishlamasa (masalan pg_dump topilmasa,
        # yoki kanalga yuborishda xato bo'lsa), bu haqda birinchi admin'ga xabar beramiz —
        # jim qolib, muammoni sezmasdan qolib ketmaslik uchun.
        await bot.send_message(
            chat_id=config.ADMINS[0],
            text=f"⚠️ Backup jarayonida xatolik yuz berdi:\n<code>{e}</code>",
            parse_mode="HTML",
        )

    finally:
        # Backup fayli kanalga muvaffaqiyatli yuborilgandan so'ng,
        # uni serverdan o'chiramiz — disk joyi asta-sekin to'lib qolmasligi uchun.
        # Fayl endi faqat Telegram kanalida saqlanadi.
        if filepath and os.path.exists(filepath):
            os.remove(filepath)