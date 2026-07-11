# keyboards/inline_keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_subscription_keyboard(channel_url: str) -> InlineKeyboardMarkup:
    """ Obuna bo'lish va tekshirish tugmalarini qaytaradi """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Kanalga obuna bo'lish 📢", url=channel_url)
            ],
            [
                InlineKeyboardButton(text="Tekshirish ✅", callback_data="checkup")
            ],
        ]
    )
    return keyboard

# keyboards/inline_keyboards.py faylining adminlar uchun:

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from data.config import config


def get_movie_deeplink_keyboard(code: str) -> InlineKeyboardMarkup:
    """
    Kanaldagi preview post ostiga chiqadigan tugma.
    Bosilganda foydalanuvchi botga o'tib, avtomatik to'liq kinoni oladi.
    """
    url = f"https://t.me/{config.BOT_USERNAME}?start={code}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎬 Kinoni olish", url=url)]
        ]
    )


def get_subscription_keyboard(channels: list[dict]) -> InlineKeyboardMarkup:
    """
    Foydalanuvchi obuna bo'lmagan kanallar ro'yxati + "Tekshirish" tugmasi.
    """
    buttons = []
    for channel in channels:
        username = channel["channel_username"]
        if username:
            url = f"https://t.me/{username}"
            buttons.append([InlineKeyboardButton(text=f"📢 {channel['channel_name']}", url=url)])

    buttons.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_confirm_delete_keyboard(code: str) -> InlineKeyboardMarkup:
    """
    Kino o'chirishdan oldin admin uchun tasdiqlash tugmasi (xato bosishning oldini olish).
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"confirm_delete:{code}"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_delete"),
            ]
        ]
    )