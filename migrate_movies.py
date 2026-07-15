"""
migrate_movies.py — Eski botdan kinolarni raqam bo'yicha so'rab,
arxiv kanaliga (yangi caption bilan) nusxa ko'chirib, asosiy PostgreSQL
bazamizga (movies jadvali) saqlovchi userbot skripti.

Barcha sozlamalar .env fayldan (data/config.py orqali) o'qiladi.
"""

import asyncio
import random
import re

from pyrogram import Client, filters
from pyrogram.types import Message

from data.config import config
from data.database import db
from data.db_commands import add_movie, add_movie_episode, code_exists_anywhere

def process_caption(caption: str | None) -> str | None:
    """
    Eski botdan kelgan caption'ni tozalab, yangi botga moslashtiradi:
    1. "Yuklash: ..." qatorini olib tashlaydi
    2. Eski bot username'ini yangi bot username'i bilan almashtiradi
    """
    if not caption:
        return caption

    lines = caption.split("\n")
    # "Yuklash" so'zi bor qatorlarni olib tashlaymiz
    filtered_lines = [line for line in lines if "Yuklash" not in line]

    text = "\n".join(filtered_lines)

    # Har qanday "@...bot" ko'rinishidagi username'ni yangi bot bilan almashtiramiz
    text = re.sub(r"@\w+bot\b", f"@{config.BOT_USERNAME}", text, flags=re.IGNORECASE)

    # Ortiqcha qolib ketgan bo'sh qatorlarni tozalaymiz (masalan Yuklash o'chgach qolgan bo'sh joy)
    text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)

    return text.strip()

# ==================== SOZLAMALAR ====================

SESSION_NAME = "migrate_userbot"

MIN_DELAY = 2.3
MAX_DELAY = 2.8

RESPONSE_TIMEOUT = 20

ADDED_BY_ID = config.ADMINS[0] if config.ADMINS else 0


# ==================== USERBOT ====================

app = Client(SESSION_NAME, api_id=config.TELEGRAM_API_ID, api_hash=config.TELEGRAM_API_HASH)

pending_future: asyncio.Future | None = None


@app.on_message(filters.chat(config.OLD_BOT_USERNAME))
async def catch_bot_reply(client: Client, message: Message):
    if not (message.video or message.document):
        return

    global pending_future
    if not pending_future or pending_future.done():
        return

    if message.media_group_id:
        # Albom (serial) — to'liq guruhni serverdan qayta so'raymiz
        try:
            album = await client.get_media_group(message.chat.id, message.id)
        except Exception:
            album = [message]
        pending_future.set_result(album)
    else:
        pending_future.set_result([message])

async def wait_for_reply(timeout: int = RESPONSE_TIMEOUT):
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

    # Pyrogram session'ga arxiv kanalini "tanitib qo'yamiz" — aks holda
    # yangi sessiyada bu kanal "topilmadi" xatosi chiqadi.
    print("📂 Barcha dialoglar yuklanmoqda (bir martalik, biroz vaqt olishi mumkin)...")
    count = 0
    async for dialog in app.get_dialogs():
        count += 1
        if dialog.chat.id == config.ARCHIVE_CHANNEL_ID:
            print(f"✅ Arxiv kanal topildi: {dialog.chat.title}")
    print(f"📂 Jami {count} ta dialog yuklandi.")

    new_code = config.MIGRATE_START_FROM
    print(f"🚀 Ko'chirish boshlandi. START_FROM={config.MIGRATE_START_FROM}, COUNT={config.MIGRATE_COUNT}")

    for old_number in range(1, config.MIGRATE_COUNT + 1):
        try:
            code_str = str(new_code)

            if await code_exists_anywhere(code_str):
                print(f"⚠️  Kod {code_str} allaqachon bazada mavjud, o'tkazib yuborildi.")
                new_code += 1
                continue

            pending_future = asyncio.get_event_loop().create_future()

            print(f"📤 {old_number}-raqam eski botga yuborilmoqda...")
            await app.send_message(config.OLD_BOT_USERNAME, str(old_number))

            messages = await wait_for_reply()

            if not messages:
                print(f"⚠️  {old_number} uchun javob kelmadi (timeout). O'tkazib yuborildi.")
                await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
                continue

            if len(messages) == 1:
                # Oddiy, bitta qismli kino
                msg = messages[0]
                if msg.video:
                    file_id, file_type = msg.video.file_id, "video"
                elif msg.document:
                    file_id, file_type = msg.document.file_id, "document"
                else:
                    print(f"⚠️  {old_number} — video/document emas, o'tkazib yuborildi.")
                    await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
                    continue

                new_caption = process_caption(msg.caption) or code_str
                await msg.copy(config.ARCHIVE_CHANNEL_ID, caption=new_caption)

                await add_movie(
                    code=code_str, title=None, file_id=file_id,
                    file_type=file_type, added_by=ADDED_BY_ID,
                )
                print(f"✅ Eski #{old_number} → Yangi kod {code_str} saqlandi (1 qism)")

            else:
                # Albom — serial, bir nechta qism
                episode_num = 1
                for msg in messages:
                    if msg.video:
                        file_id, file_type = msg.video.file_id, "video"
                    elif msg.document:
                        file_id, file_type = msg.document.file_id, "document"
                    else:
                        continue

                    new_caption = process_caption(msg.caption) or f"{code_str} - {episode_num}-qism"
                    await msg.copy(config.ARCHIVE_CHANNEL_ID, caption=new_caption)

                    await add_movie_episode(
                        code=code_str, episode_number=episode_num,
                        file_id=file_id, file_type=file_type,
                    )
                    episode_num += 1

                print(f"✅ Eski #{old_number} → Yangi kod {code_str} saqlandi ({episode_num - 1} qism, serial)")

            new_code += 1

        except Exception as e:
            print(f"❌ {old_number}-raqamda xatolik: {e}. Davom etamiz...")

        await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
    await db.close_pool()
    print("🎉 Ko'chirish yakunlandi!")

    # Migratsiya tugagach, dasturni to'xtatamiz
    app.stop()


async def start_migration():
    await migrate()


if __name__ == "__main__":
    app.start()
    asyncio.get_event_loop().run_until_complete(migrate())
    app.stop()