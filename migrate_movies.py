"""
migrate_movies.py — Eski botdan kinolarni raqam bo'yicha so'rab,
arxiv kanaliga (yangi caption bilan) nusxa ko'chirib, asosiy PostgreSQL
bazamizga (movies jadvali) saqlovchi userbot skripti.

Barcha sozlamalar .env fayldan (data/config.py orqali) o'qiladi.
"""

import asyncio
import random

from pyrogram import Client, filters
from pyrogram.types import Message

from data.config import config
from data.database import db
from data.db_commands import add_movie, check_code_exists

# ==================== SOZLAMALAR ====================

SESSION_NAME = "migrate_userbot"

MIN_DELAY = 2.3
MAX_DELAY = 2.8

RESPONSE_TIMEOUT = 20

ADDED_BY_ID = config.ADMINS[0] if config.ADMINS else 0


# ==================== USERBOT ====================

app = Client(SESSION_NAME, api_id=config.TELEGRAM_API_ID, api_hash=config.TELEGRAM_API_HASH)

# "Kutish"ni saqlab turuvchi global o'zgaruvchi.
# Xabar yuborishdan OLDIN yaratiladi — shunda tez javob beruvchi botlarda
# ham javobni o'tkazib yubormaymiz (race condition oldini olish).
pending_future: asyncio.Future | None = None


@app.on_message(filters.chat(config.OLD_BOT_USERNAME))
async def catch_bot_reply(client: Client, message: Message):
    """
    Eski botdan KELGAN HAR QANDAY xabarni ushlaydi (debug uchun),
    lekin faqat video/document bo'lsa, kutuvga topshiradi.
    """
    print(
        f"📨 Eski botdan xabar keldi — "
        f"text={bool(message.text)}, video={bool(message.video)}, "
        f"document={bool(message.document)}"
    )

    if not (message.video or message.document):
        return

    global pending_future
    if pending_future and not pending_future.done():
        pending_future.set_result(message)


async def wait_for_reply(timeout: int = RESPONSE_TIMEOUT) -> Message | None:
    """
    Eski botdan javob kelishini kutadi. `pending_future` chaqiruvchi tomonidan
    OLDINDAN yaratilgan bo'lishi shart (xabar yuborishdan oldin).
    """
    global pending_future
    try:
        return await asyncio.wait_for(pending_future, timeout=timeout)
    except asyncio.TimeoutError:
        return None
    finally:
        pending_future = None


async def migrate():
    global pending_future

    await db.create_pool()

    new_code = config.MIGRATE_START_FROM
    print(f"🚀 Ko'chirish boshlandi. START_FROM={config.MIGRATE_START_FROM}, COUNT={config.MIGRATE_COUNT}")

    for old_number in range(1, config.MIGRATE_COUNT + 1):
        code_str = str(new_code)

        if await check_code_exists(code_str):
            print(f"⚠️  Kod {code_str} allaqachon bazada mavjud, o'tkazib yuborildi.")
            new_code += 1
            continue

        # Avval "kutish"ni tayyorlab qo'yamiz — keyin xabar yuboramiz
        pending_future = asyncio.get_event_loop().create_future()

        print(f"📤 {old_number}-raqam eski botga yuborilmoqda...")
        await app.send_message(config.OLD_BOT_USERNAME, str(old_number))

        reply = await wait_for_reply()

        if reply is None:
            print(f"⚠️  {old_number} uchun javob kelmadi (timeout). O'tkazib yuborildi.")
            await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
            continue

        if reply.video:
            file_id = reply.video.file_id
            file_type = "video"
        elif reply.document:
            file_id = reply.document.file_id
            file_type = "document"
        else:
            print(f"⚠️  {old_number} — video/document emas, o'tkazib yuborildi.")
            await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
            continue

        # Arxiv kanaliga nusxa — ESKI caption'ni e'tiborsiz qoldirib,
        # YANGI caption sifatida faqat kod raqamini qo'yamiz
        await reply.copy(config.ARCHIVE_CHANNEL_ID, caption=code_str)

        await add_movie(
            code=code_str,
            title=None,
            file_id=file_id,
            file_type=file_type,
            added_by=ADDED_BY_ID,
        )

        print(f"✅ Eski #{old_number} → Yangi kod {code_str} saqlandi ({file_type})")

        new_code += 1
        await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    await db.close_pool()
    print("🎉 Ko'chirish yakunlandi!")


async def main():
    async with app:
        await migrate()


if __name__ == "__main__":
    asyncio.run(main())