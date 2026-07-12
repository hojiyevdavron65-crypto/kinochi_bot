from aiogram import Bot
from aiogram.filters import BaseFilter
from aiogram.types import Message

from data.config import config
from data.db_commands import get_required_channels, has_join_request


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in config.ADMINS


class IsSubscribed(BaseFilter):
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
    """
    Foydalanuvchi obuna hisoblanadimi — ikki holatda True qaytaradi:
    1. Haqiqatan kanalga a'zo bo'lsa (member/admin/creator)
    2. Hali a'zo bo'lmasa-da, qo'shilish so'rovini yuborgan bo'lsa
       (admin keyinroq tasdiqlaguncha ham botdan foydalanishi mumkin)
    """
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        if member.status in ("member", "administrator", "creator"):
            return True
    except Exception:
        pass

    # Haqiqiy a'zo bo'lmasa ham, so'rov yuborilgan bo'lsa — o'tkazamiz
    return await has_join_request(user_id, channel_id)


async def get_unsubscribed_channels(bot: Bot, user_id: int) -> list[dict]:
    channels = await get_required_channels()
    unsubscribed = []

    for channel in channels:
        if not await _is_user_subscribed(bot, channel["channel_id"], user_id):
            unsubscribed.append(channel)

    return unsubscribed