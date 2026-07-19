import asyncio

from aiogram import Router, F
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile

from data.config import config
from data.db_commands import (
    add_movie,
    add_episode,
    code_exists,
    delete_movie,
    get_movie,
    get_movies_count,
    get_users_count,
    get_all_users,
)
from filters.filters import IsAdmin
from handlers.admin_states import AddMovie, AddEpisode, DeleteMovie, Broadcast

admin_router = Router()
admin_router.message.filter(IsAdmin())


# ==================== KINO QO'SHISH ====================

@admin_router.message(Command("add"))
async def cmd_add_movie(message: Message, state: FSMContext):
    await message.answer(
        "🎬 Kino faylini (video yoki hujjat) yuboring.\n\n"
        "Bekor qilish uchun /cancel"
    )
    await state.set_state(AddMovie.waiting_for_file)


@admin_router.message(AddMovie.waiting_for_file, F.video | F.document)
async def process_movie_file(message: Message, state: FSMContext):
    if message.video:
        file_id, file_type = message.video.file_id, "video"
    else:
        file_id, file_type = message.document.file_id, "document"

    await message.forward(chat_id=config.ARCHIVE_CHANNEL_ID)
    await state.update_data(file_id=file_id, file_type=file_type)
    await message.answer("✅ Fayl qabul qilindi.\n\n🔢 Endi kod kiriting:")
    await state.set_state(AddMovie.waiting_for_code)


@admin_router.message(AddMovie.waiting_for_file)
async def process_wrong_file(message: Message):
    await message.answer("⚠️ Iltimos, video yoki hujjat (fayl) ko'rinishida yuboring.")


@admin_router.message(AddMovie.waiting_for_code, F.text)
async def process_movie_code(message: Message, state: FSMContext):
    code = message.text.strip()

    if len(code) > 50:
        await message.answer("⚠️ Kod juda uzun (maksimum 50 belgi). Qisqaroq kod kiriting:")
        return

    if await code_exists(code):
        await message.answer(
            f"❌ <b>{code}</b> kodi allaqachon band.\n\n"
            f"Shu kodga yangi qism qo'shish uchun /addepisode buyrug'ini ishlating.",
            parse_mode="HTML",
        )
        return

    await state.update_data(code=code)
    await message.answer(
        "📝 Kino haqida caption yozing (arxiv kanalda ko'rsatiladi):\n\n"
        "Masalan:\n<code>Пэрл / Pearl 2022\nRus tilida</code>\n\n"
        "Caption yozmoqchi bo'lmasangiz /skip bosing:",
        parse_mode="HTML",
    )
    await state.set_state(AddMovie.waiting_for_caption)


@admin_router.message(AddMovie.waiting_for_caption, Command("skip"))
async def skip_caption(message: Message, state: FSMContext):
    await finalize_add_movie(message, state, caption=None)


@admin_router.message(AddMovie.waiting_for_caption, F.text)
async def process_movie_caption(message: Message, state: FSMContext):
    await finalize_add_movie(message, state, caption=message.text.strip())


async def finalize_add_movie(message: Message, state: FSMContext, caption: str | None):
    data = await state.get_data()
    full_caption = (
        f"Kod: {data['code']}\n\n{caption}\n\n🤖 Bizning bot: @{config.BOT_USERNAME}"
        if caption
        else f"Kod: {data['code']}\n\n🤖 Bizning bot: @{config.BOT_USERNAME}"
    )

    await add_movie(
        code=data["code"],
        file_id=data["file_id"],
        file_type=data["file_type"],
        added_by=message.from_user.id,
        caption=full_caption,
    )

    await message.answer(
        f"✅ Kino qo'shildi!\n\n🔢 Kod: <b>{data['code']}</b>",
        parse_mode="HTML",
    )
    await state.clear()


# ==================== MAVJUD KODGA YANGI QISM QO'SHISH ====================

@admin_router.message(Command("addepisode"))
async def cmd_add_episode(message: Message, state: FSMContext):
    await message.answer(
        "📺 Qaysi kodga yangi qism qo'shmoqchisiz? Kodni kiriting:\n\n"
        "Bekor qilish uchun /cancel"
    )
    await state.set_state(AddEpisode.waiting_for_code)


@admin_router.message(AddEpisode.waiting_for_code, F.text)
async def process_episode_code(message: Message, state: FSMContext):
    code = message.text.strip()
    rows = await get_movie(code)

    if not rows:
        await message.answer(
            f"❌ <b>{code}</b> kodli kino topilmadi. Avval /add orqali asosiy kinoni qo'shing.",
            parse_mode="HTML",
        )
        return

    # Mavjud qismlar sonini aniqlaymiz
    existing_episodes = [r for r in rows if r["episode_number"] is not None]
    next_episode = len(existing_episodes) + 1

    await state.update_data(code=code, episode_number=next_episode)
    await message.answer(
        f"✅ <b>{code}</b> kodi topildi.\n\n"
        f"📺 Mavjud qismlar: {len(existing_episodes)} ta\n"
        f"➕ Yangi qism raqami: <b>{next_episode}</b>\n\n"
        f"Endi <b>{next_episode}-qism</b> faylini yuboring:",
        parse_mode="HTML",
    )
    await state.set_state(AddEpisode.waiting_for_file)


@admin_router.message(AddEpisode.waiting_for_file, F.video | F.document)
async def process_episode_file(message: Message, state: FSMContext):
    if message.video:
        file_id, file_type = message.video.file_id, "video"
    else:
        file_id, file_type = message.document.file_id, "document"

    await message.forward(chat_id=config.ARCHIVE_CHANNEL_ID)
    await state.update_data(file_id=file_id, file_type=file_type)
    await message.answer(
        "✅ Fayl qabul qilindi.\n\n"
        "📝 Bu qism uchun caption yozing (yoki /skip):"
    )
    await state.set_state(AddEpisode.waiting_for_caption)


@admin_router.message(AddEpisode.waiting_for_file)
async def process_episode_wrong_file(message: Message):
    await message.answer("⚠️ Iltimos, video yoki hujjat ko'rinishida yuboring.")


@admin_router.message(AddEpisode.waiting_for_caption, Command("skip"))
async def skip_episode_caption(message: Message, state: FSMContext):
    await finalize_add_episode(message, state, caption=None)


@admin_router.message(AddEpisode.waiting_for_caption, F.text)
async def process_episode_caption(message: Message, state: FSMContext):
    await finalize_add_episode(message, state, caption=message.text.strip())


async def finalize_add_episode(message: Message, state: FSMContext, caption: str | None):
    data = await state.get_data()
    full_caption = (
        f"Kod: {data['code']} | {data['episode_number']}-qism\n\n{caption}\n\n"
        f"🤖 Bizning bot: @{config.BOT_USERNAME}"
        if caption
        else
        f"Kod: {data['code']} | {data['episode_number']}-qism\n\n"
        f"🤖 Bizning bot: @{config.BOT_USERNAME}"
    )

    await add_episode(
        code=data["code"],
        episode_number=data["episode_number"],
        file_id=data["file_id"],
        file_type=data["file_type"],
        added_by=message.from_user.id,
        caption=full_caption,
    )

    await message.answer(
        f"✅ {data['episode_number']}-qism qo'shildi!\n\n"
        f"🔢 Kod: <b>{data['code']}</b>",
        parse_mode="HTML",
    )
    await state.clear()


# ==================== KINO O'CHIRISH ====================

@admin_router.message(Command("delete"))
async def cmd_delete_movie(message: Message, state: FSMContext):
    await message.answer("🗑 O'chirmoqchi bo'lgan kino kodini kiriting:")
    await state.set_state(DeleteMovie.waiting_for_code)


@admin_router.message(DeleteMovie.waiting_for_code, F.text)
async def process_delete_code(message: Message, state: FSMContext):
    code = message.text.strip()
    rows = await get_movie(code)

    if not rows:
        await message.answer(f"❌ <b>{code}</b> kodli kino topilmadi.", parse_mode="HTML")
        await state.clear()
        return

    await delete_movie(code)
    await message.answer(f"✅ <b>{code}</b> kodli kino o'chirildi.", parse_mode="HTML")
    await state.clear()


# ==================== BEKOR QILISH ====================

@admin_router.message(Command("cancel"))
async def cancel_action(message: Message, state: FSMContext):
    if await state.get_state() is None:
        return
    await state.clear()
    await message.answer("❌ Bekor qilindi.")


# ==================== STATISTIKA ====================

@admin_router.message(Command("stats"))
async def cmd_stats(message: Message):
    movies_count = await get_movies_count()
    users_count = await get_users_count()
    await message.answer(
        f"📊 <b>Statistika</b>\n\n"
        f"🎬 Kinolar soni: {movies_count}\n"
        f"👥 Foydalanuvchilar soni: {users_count}",
        parse_mode="HTML",
    )


# ==================== BROADCAST ====================

@admin_router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    await message.answer(
        "📢 Yubormoqchi bo'lgan xabaringizni yuboring.\n\nBekor qilish uchun /cancel"
    )
    await state.set_state(Broadcast.waiting_for_message)


@admin_router.message(Broadcast.waiting_for_message)
async def process_broadcast(message: Message, state: FSMContext):
    await state.clear()
    users = await get_all_users()
    status_msg = await message.answer(f"⏳ Yuborilmoqda... 0/{len(users)}")

    success, failed = 0, 0
    for i, user in enumerate(users, start=1):
        try:
            await message.copy_to(chat_id=user["user_id"])
            success += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            failed += 1
        except Exception:
            failed += 1

        if i % 30 == 0:
            await asyncio.sleep(1)
            await status_msg.edit_text(f"⏳ Yuborilmoqda... {i}/{len(users)}")

    await status_msg.edit_text(
        f"✅ Broadcast tugadi!\n\n✅ Yuborildi: {success}\n❌ Yuborilmadi: {failed}"
    )