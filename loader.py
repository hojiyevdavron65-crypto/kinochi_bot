from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from data.config import config

# Bot obyekti — Telegram API bilan aloqa qiluvchi asosiy obyekt.
# DefaultBotProperties orqali parse_mode="HTML" ni global qilib belgilaymiz —
# shunda har bir message.answer() ichida alohida parse_mode="HTML" yozish shart emas.
bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

# MemoryStorage — FSM holatlarini (masalan AddMovie.waiting_for_code) RAM'da saqlaydi.
# Bot qayta ishga tushirilsa, hozirgi holatlar (state) yo'qoladi — kichik/o'rta loyihalar
# uchun yetarli. Katta yuklamada Redis storage'ga almashtirish mumkin bo'ladi.
dp = Dispatcher(storage=MemoryStorage())