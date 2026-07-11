from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from data.config import config

# Local Bot API serverga ulanish — 20 MB o'rniga 2000 MB (2 GB) gacha
# fayl yuklab olish imkonini beradi.
local_server = TelegramAPIServer.from_base(
    "http://telegram-bot-api:8081",
    is_local=True,
)

bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    session=AiohttpSession(api=local_server),
)

dp = Dispatcher(storage=MemoryStorage())