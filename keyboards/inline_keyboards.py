from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from data.config import config


def get_movie_deeplink_keyboard(code: str) -> InlineKeyboardMarkup:
    url = f"https://t.me/{config.BOT_USERNAME}?start={code}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎬 Kinoni olish", url=url)]
        ]
    )


async def get_subscription_keyboard(bot: Bot, channels: list[dict]) -> InlineKeyboardMarkup:
    """
    Foydalanuvchi obuna bo'lmagan kanallar ro'yxati + "Tekshirish" tugmasi.

    Public kanallar uchun — @username orqali oddiy havola.
    Private kanallar uchun — bot avtomatik invite link yaratadi
    (bot kanalda admin bo'lgani uchun bu har doim ishlaydi).
    """
    buttons = []

    for channel in channels:
        username = channel["channel_username"]

        if username:
            url = f"https://t.me/{username}"
        else:
            try:
                invite = await bot.create_chat_invite_link(chat_id=channel["channel_id"])
                url = invite.invite_link
            except Exception:
                # Agar invite link yaratib bo'lmasa (masalan bot admin emas),
                # bu kanalni tugmalar ro'yxatiga qo'shmaymiz — lekin obuna
                # tekshiruvida u baribir hisobga olinadi.
                continue

        buttons.append([InlineKeyboardButton(text=f"📢 {channel['channel_name']}", url=url)])

    buttons.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)