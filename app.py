import asyncio
import logging

from data.database import db
from handlers import router
from loader import bot, dp
from middlewares import ThrottlingMiddleware
from utils.scheduler import setup_scheduler


async def on_startup() -> None:
    """
    Bot ishga tushishidan oldin bajariladigan tayyorgarlik ishlari:
    - Database bilan bog'lanish (connection pool ochish)
    - Kerakli jadvallarni yaratish (agar hali mavjud bo'lmasa)
    - Kunlik avtomatik backup vazifasini rejalashtirish
    """
    await db.create_pool()
    await db.create_tables()

    setup_scheduler(bot)

    logging.info("Bot muvaffaqiyatli ishga tushdi.")


async def on_shutdown() -> None:
    """
    Bot to'xtatilganda bajariladigan tozalash ishlari:
    - Database connection pool'ni yopish (resurslarni bo'shatish)
    """
    await db.close_pool()
    logging.info("Bot to'xtatildi, database pool yopildi.")


async def main() -> None:
    # Loglarni konsolga chiqarish — xatoliklarni va bot holatini kuzatish uchun
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    # Middleware'larni ulaymiz — har bir kelgan xabar avval shu middleware'dan o'tadi
    dp.message.middleware(ThrottlingMiddleware(limit=1.0))

    # Barcha handlerlarni (admin, kanal, foydalanuvchi) birlashtiruvchi asosiy routerni ulaymiz
    dp.include_router(router)

    # Startup va shutdown funksiyalarini ro'yxatdan o'tkazamiz —
    # dp.start_polling() ishga tushganda avtomatik chaqiriladi
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Eski (bot to'xtatilgan paytda kelgan) xabarlarni tashlab yuborib,
    # botni pollingda ishga tushiramiz
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi (qo'lda to'xtatish).")