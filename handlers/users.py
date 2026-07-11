from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery

from data.db_commands import add_user, check_user_exists, get_movie_by_code
from filters.filters import IsSubscribed, get_unsubscribed_channels
from keyboards.inline_keyboards import get_subscription_keyboard

user_router = Router()


# ==================== YORDAMCHI FUNKSIYALAR ====================

async def send_movie(message: Message, movie):
    caption = f"🎬 {movie['title']}" if movie["title"] else None
    if movie["file_type"] == "video":
        await message.answer_video(video=movie["file_id"], caption=caption, parse_mode="HTML")
    else:
        await message.answer_document(document=movie["file_id"], caption=caption, parse_mode="HTML")


# ==================== /start ====================

@user_router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, bot: Bot):
    if not await check_user_exists(message.from_user.id):
        await add_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )

    unsubscribed = await get_unsubscribed_channels(bot, message.from_user.id)
    if unsubscribed:
        keyboard = await get_subscription_keyboard(bot, unsubscribed)
        await message.answer(
            "📢 Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
            reply_markup=keyboard,
        )
        return

    if command.args:
        code = command.args.strip()
        movie = await get_movie_by_code(code)
        if movie:
            await send_movie(message, movie)
            return
        await message.answer(f"❌ <b>{code}</b> kodli kino topilmadi.", parse_mode="HTML")
        return

    await message.answer(
        "🎬 <b>Kinochi Bot</b> ga xush kelibsiz!\n\n"
        "Kino kodini yuboring, men sizga kinoni topib beraman.",
        parse_mode="HTML",
    )


# ==================== OBUNANI TEKSHIRISH (callback) ====================

@user_router.callback_query(F.data == "check_sub")
async def check_subscription_callback(callback: CallbackQuery, bot: Bot):
    unsubscribed = await get_unsubscribed_channels(bot, callback.from_user.id)

    if unsubscribed:
        await callback.answer("❌ Siz hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True)
        return

    await callback.message.delete()
    await callback.message.answer(
        "✅ Obuna tasdiqlandi!\n\n"
        "Kino kodini yuboring, men sizga kinoni topib beraman.",
        parse_mode="HTML",
    )
    await callback.answer()


# ==================== KINO QIDIRISH (kod orqali) ====================

@user_router.message(IsSubscribed(), F.text.regexp(r"^\S+$"))
async def search_movie(message: Message):
    code = message.text.strip()
    movie = await get_movie_by_code(code)

    if not movie:
        await message.answer(f"❌ <b>{code}</b> kodli kino topilmadi.", parse_mode="HTML")
        return

    await send_movie(message, movie)


# ==================== OBUNA BO'LMAGANLAR UCHUN FALLBACK ====================

@user_router.message(F.text.regexp(r"^\S+$"))
async def require_subscription(message: Message, bot: Bot):
    unsubscribed = await get_unsubscribed_channels(bot, message.from_user.id)
    keyboard = await get_subscription_keyboard(bot, unsubscribed)
    await message.answer(
        "📢 Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
        reply_markup=keyboard,
    )