import asyncio

from aiogram import Router, F
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from data.config import config
from data.db_commands import (
    add_movie,
    check_code_exists,
    delete_movie,
    get_movie_by_code,
    get_all_movies_count,
    get_users_count,
    get_all_users,
)
from filters.filters import IsAdmin
from handlers.admin_states import AddMovie, DeleteMovie, Broadcast

admin_router = Router()
admin_router.message.filter(IsAdmin())


# ==================== KINO QO'SHISH ====================

@admin_router.message(Command("add"))
async def cmd_add_movie(message: Message, state: FSMContext):
    await message.answer(
        "🎬 Kino faylini (video yoki hujjat) yuboring.\n\nBekor qilish uchun /cancel"
    )
    await state.set_state(AddMovie.waiting_for_file)


@admin_router.message(AddMovie.waiting_for_file, F.video | F.document)
async def process_movie_file(message: Message, state: FSMContext):
    if message.video:
        file_id = message.video.file_id
        file_type = "video"
    else:
        file_id = message.document.file_id
        file_type = "document"

    # Faylni zaxira sifatida yashirin arxiv kanaliga forward qilamiz
    await message.forward(chat_id=config.ARCHIVE_CHANNEL_ID)

    await state.update_data(file_id=file_id, file_type=file_type)
    await message.answer("✅ Fayl qabul qilindi.\n\n🔢 Endi shu kino uchun kod kiriting:")
    await state.set_state(AddMovie.waiting_for_code)


@admin_router.message(AddMovie.waiting_for_file)
async def process_wrong_file(message: Message):
    await message.answer("⚠️ Iltimos, video yoki hujjat (fayl) ko'rinishida yuboring.")


@admin_router.message(AddMovie.waiting_for_code, F.text)
async def process_movie_code(message: Message, state: FSMContext):
    code = message.text.strip()

    if await check_code_exists(code):
        await message.answer(
            f"❌ <b>{code}</b> kodi allaqachon band. Boshqa kod kiriting:",
            parse_mode="HTML",
        )
        return

    await state.update_data(code=code)
    await message.answer("📝 Endi kino nomini kiriting:")
    await state.set_state(AddMovie.waiting_for_title)


@admin_router.message(AddMovie.waiting_for_title, F.text)
async def process_movie_title(message: Message, state: FSMContext):
    title = message.text.strip()
    data = await state.get_data()

    await add_movie(
        code=data["code"],
        title=title,
        file_id=data["file_id"],
        file_type=data["file_type"],
        added_by=message.from_user.id,
    )

    await message.answer(
        f"✅ Kino bazaga qo'shildi!\n\n"
        f"🔢 Kod: <b>{data['code']}</b>\n"
        f"🎬 Nom: {title}",
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
    movie = await get_movie_by_code(code)

    if not movie:
        await message.answer(f"❌ <b>{code}</b> kodli kino topilmadi.", parse_mode="HTML")
        await state.clear()
        return

    await delete_movie(code)
    await message.answer(f"✅ <b>{code}</b> kodli kino o'chirildi.", parse_mode="HTML")
    await state.clear()


# ==================== BEKOR QILISH ====================

@admin_router.message(Command("cancel"))
async def cancel_action(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.answer("❌ Bekor qilindi.")


# ==================== STATISTIKA ====================

@admin_router.message(Command("stats"))
async def cmd_stats(message: Message):
    movies_count = await get_all_movies_count()
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
        "📢 Yubormoqchi bo'lgan xabaringizni yuboring (matn, rasm, video — hammasi bo'ladi).\n\n"
        "Bekor qilish uchun /cancel"
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