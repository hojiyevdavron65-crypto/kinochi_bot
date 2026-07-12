from aiogram import Bot
from aiogram.filters import BaseFilter
from aiogram.types import Message

from data.config import config
from data.db_commands import get_required_channels


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in config.ADMINS


class IsSubscribed(BaseFilter):
    """
    Foydalanuvchi barcha majburiy kanallarga obuna bo'lganini tekshiradi.
    Adminlar tekshiruvdan chetlab o'tadi.
    """

    async def __call__(self, message: Message, bot: Bot) -> bool:
        if message.from_user.id in config.ADMINS:
            return True

        channels = await get_required_channels()
        if not channels:
            return True

        for channel in channels:
            if not await _is_user_subscribed(bot, channel["channel_id"], message.from_user.id):
                return False

        return True


async def _is_user_subscribed(bot: Bot, channel_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        # Bot kanalda admin bo'lmasa yoki boshqa xato bo'lsa — obuna emas deb hisoblaymiz
        return False


async def get_unsubscribed_channels(bot: Bot, user_id: int) -> list[dict]:
    """
    Foydalanuvchi obuna bo'lmagan kanallar ro'yxatini qaytaradi.
    Handler ichida "Obuna bo'ling" tugmalarini chiqarish uchun ishlatiladi.
    """
    channels = await get_required_channels()
    unsubscribed = []

    for channel in channels:
        if not await _is_user_subscribed(bot, channel["channel_id"], user_id):
            unsubscribed.append(channel)

    return unsubscribed