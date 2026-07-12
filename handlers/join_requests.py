from aiogram import Router, F
from aiogram.types import ChatJoinRequest, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from data.config import config
from data.db_commands import add_join_request

join_router = Router()


@join_router.chat_join_request()
async def handle_join_request(request: ChatJoinRequest):
    """
    Yangi qo'shilish so'rovi kelganda:
    1. Bazaga "so'rov yuborilgan" deb yozib qo'yamiz — bu foydalanuvchiga
       darhol botdan foydalanish huquqini beradi (admin tasdiqlashini kutmasdan).
    2. Admin(lar)ga tasdiqlash/rad etish tugmalari bilan xabar yuboramiz.
    """
    user = request.from_user
    chat = request.chat

    # 1-qadam — darhol botdan foydalanish huquqini ochamiz
    await add_join_request(user_id=user.id, channel_id=chat.id)

    # 2-qadam — admin(lar)ga xabar
    text = (
        f"📥 <b>Yangi qo'shilish so'rovi</b>\n\n"
        f"👤 Foydalanuvchi: {user.full_name}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📢 Kanal: {chat.title}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_join:{chat.id}:{user.id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"decline_join:{chat.id}:{user.id}"),
            ]
        ]
    )

    for admin_id in config.ADMINS:
        await request.bot.send_message(chat_id=admin_id, text=text, reply_markup=keyboard, parse_mode="HTML")


@join_router.callback_query(F.data.startswith("approve_join:"))
async def approve_join_request(callback: CallbackQuery):
    _, chat_id, user_id = callback.data.split(":")
    chat_id, user_id = int(chat_id), int(user_id)

    try:
        await callback.bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
        await callback.message.edit_text(callback.message.text + "\n\n✅ <b>Tasdiqlandi</b>", parse_mode="HTML")
    except Exception as e:
        await callback.answer(f"Xatolik: {e}", show_alert=True)
        return

    await callback.answer("Foydalanuvchi kanalga qo'shildi ✅")


@join_router.callback_query(F.data.startswith("decline_join:"))
async def decline_join_request(callback: CallbackQuery):
    _, chat_id, user_id = callback.data.split(":")
    chat_id, user_id = int(chat_id), int(user_id)

    try:
        await callback.bot.decline_chat_join_request(chat_id=chat_id, user_id=user_id)
        await callback.message.edit_text(callback.message.text + "\n\n❌ <b>Rad etildi</b>", parse_mode="HTML")
    except Exception as e:
        await callback.answer(f"Xatolik: {e}", show_alert=True)
        return

    await callback.answer("Foydalanuvchi rad etildi ❌")