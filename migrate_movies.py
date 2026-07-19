"""
migrate_movies.py — To'liq qayta yozilgan versiya.

Caption formatlari:
    Arxiv kanalga:
        Eski kod: 4052 | Yangi kod: 4100

        Пэрл / Pearl 2022 (ViruseProject [1080p]) Rus tilida

        🤖 Bizning bot: @kino_officalbot

    Foydalanuvchiga (eski kod yo'q, t.me yo'q):
        Пэрл / Pearl 2022 (ViruseProject [1080p]) Rus tilida

        🤖 Bizning bot: @kino_officalbot
"""

import asyncio
import random
import re

from pyrogram import Client
from pyrogram.errors import FloodWait

from data.config import config
from data.database import db
from data.db_commands import add_movie, add_episode, code_exists

SESSION_NAME = "migrate_userbot"
MIN_DELAY = 4.0
MAX_DELAY = 6.0
RESPONSE_TIMEOUT = 30
ADDED_BY_ID = config.ADMINS[0] if config.ADMINS else 0

app = Client(SESSION_NAME, api_id=config.TELEGRAM_API_ID, api_hash=config.TELEGRAM_API_HASH)
pending_future: asyncio.Future | None = None


def clean_caption(original: str | None) -> str:
    """
    Eski captiondan keraksiz qatorlarni olib tashlaydi:
    - Yuklash: ... qatorlari
    - Bizning bot: ... qatorlari
    - t.me/... havolalari
    - @username havolalari
    """
    if not original:
        return ""

    lines = original.split("\n")
    filtered = []
    for line in lines:
        if "Yuklash" in line:
            continue
        if "Bizning bot" in line:
            continue
        if re.search(r"t\.me/", line, re.IGNORECASE):
            continue
        if re.search(r"@\w+", line):
            continue
        filtered.append(line)

    text = "\n".join(filtered).strip()
    return re.sub(r"\n{3,}", "\n\n", text)


def build_archive_caption(old_number: int, new_code: str, original: str | None) -> str:
    """Arxiv kanalga yuboriladigan caption."""
    header = f"Eski kod: {old_number} | Yangi kod: {new_code}"
    footer = f"🤖 Bizning bot: {config.BOT_USERNAME}"
    body = clean_caption(original)

    if body:
        return f"{header}\n\n{body}\n\n{footer}"
    return f"{header}\n\n{footer}"


def build_user_caption(new_code: str, original: str | None) -> str:
    """
    Foydalanuvchiga yuboriladigan caption:
    - Birinchi qatorda yangi kod
    - Eski ma'lumotlar (tozalangan)
    - Bot username
    """
    footer = f"🤖 Bizning bot: {config.BOT_USERNAME}"
    body = clean_caption(original)

    if body:
        return f"Kod: {new_code}\n\n{body}\n\n{footer}"
    return f"Kod: {new_code}\n\n{footer}"


@app.on_message()
async def catch_message(client, message):
    if not message.chat:
        return
    chat_username = (message.chat.username or "").lower()
    bot_username = (config.OLD_BOT_USERNAME or "").lower()
    if chat_username != bot_username:
        return
    if not (message.video or message.document):
        return

    global pending_future
    if pending_future and not pending_future.done():
        if message.media_group_id:
            try:
                album = await client.get_media_group(message.chat.id, message.id)
                pending_future.set_result(album)
            except Exception:
                pending_future.set_result([message])
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


async def flood_safe(coro):
    while True:
        try:
            return await coro
        except FloodWait as e:
            wait = e.value + 10
            print(f"⏳ FloodWait: {wait} soniya kutamiz...")
            await asyncio.sleep(wait)


async def migrate():
    global pending_future

    await db.create_pool()

    print("📂 Dialoglar yuklanmoqda...")
    async for _ in app.get_dialogs():
        pass
    print("✅ Tayyor.")

    new_code = config.MIGRATE_START_FROM
    print(f"🚀 START={config.MIGRATE_START_FROM}, COUNT={config.MIGRATE_COUNT}")

    for old_number in range(1, config.MIGRATE_COUNT + 1):
        code_str = str(new_code)

        if await code_exists(code_str):
            print(f"⏭  Kod {code_str} mavjud, o'tkazildi.")
            new_code += 1
            continue

        try:
            pending_future = asyncio.get_event_loop().create_future()

            print(f"📤 Eski #{old_number} → yangi kod {code_str}")
            await flood_safe(
                app.send_message(config.OLD_BOT_USERNAME, str(old_number))
            )

            messages = await wait_for_reply()

            if not messages:
                print(f"⚠️  #{old_number} — javob kelmadi, o'tkazildi.")
                await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
                continue

            if len(messages) == 1:
                msg = messages[0]
                if msg.video:
                    file_id, file_type = msg.video.file_id, "video"
                elif msg.document:
                    file_id, file_type = msg.document.file_id, "document"
                else:
                    print(f"⚠️  #{old_number} — video/document emas.")
                    await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
                    continue

                arch_cap = build_archive_caption(old_number, code_str, msg.caption)
                user_cap = build_user_caption(code_str, msg.caption)

                await flood_safe(msg.copy(config.ARCHIVE_CHANNEL_ID, caption=arch_cap))
                await add_movie(
                    code=code_str,
                    file_id=file_id,
                    file_type=file_type,
                    added_by=ADDED_BY_ID,
                    archive_caption=arch_cap,
                    user_caption=user_cap,
                )
                print(f"✅ #{old_number} → kod {code_str} (kino)")

            else:
                for episode_num, msg in enumerate(messages, start=1):
                    if msg.video:
                        file_id, file_type = msg.video.file_id, "video"
                    elif msg.document:
                        file_id, file_type = msg.document.file_id, "document"
                    else:
                        continue

                    arch_cap = build_archive_caption(old_number, code_str, msg.caption)
                    user_cap = build_user_caption(code_str, msg.caption)

                    await flood_safe(msg.copy(config.ARCHIVE_CHANNEL_ID, caption=arch_cap))
                    await add_episode(
                        code=code_str,
                        episode_number=episode_num,
                        file_id=file_id,
                        file_type=file_type,
                        added_by=ADDED_BY_ID,
                        archive_caption=arch_cap,
                        user_caption=user_cap,
                    )

                print(f"✅ #{old_number} → kod {code_str} (serial, {len(messages)} qism)")

            new_code += 1

        except FloodWait as e:
            wait = e.value + 10
            print(f"⏳ FloodWait (tashqi): {wait} soniya, qayta urinadi...")
            await asyncio.sleep(wait)
            continue

        except Exception as e:
            print(f"❌ #{old_number} xatolik: {e}")
            new_code += 1

        await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    await db.close_pool()
    print("🎉 Ko'chirish yagunlandi!")


if __name__ == "__main__":
    app.start()
    asyncio.get_event_loop().run_until_complete(migrate())
    app.stop()