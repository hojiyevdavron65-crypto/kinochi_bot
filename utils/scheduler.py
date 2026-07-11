from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from utils.backup import send_backup_to_channel

# Scheduler global obyekt sifatida yaratiladi — bot ishga tushganda
# faqat bitta marta ishga tushiriladi va butun dastur davomida ishlab turadi.
scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")


def setup_scheduler(bot: Bot) -> None:
    """
    Kunlik avtomatik backup vazifasini rejalashtiradi.

    "cron" trigger — belgilangan aniq vaqtda (masalan har kuni soat 03:00 da)
    ishga tushadigan vazifalar uchun ishlatiladi (soat, kun, oy asosida).

    Nega soat 03:00: bu vaqtda odatda foydalanuvchilar eng kam faol bo'ladi,
    shuning uchun backup jarayoni (baza bilan ishlash) botning oddiy ishiga
    xalaqit bermaydi.
    """
    scheduler.add_job(
        send_backup_to_channel,
        trigger="cron",
        hour=3,
        minute=0,
        args=(bot,),              # send_backup_to_channel(bot) shaklida chaqiriladi
        id="daily_backup",        # vazifaning unikal nomi — qayta ishga tushirilsa dublikat bo'lmaydi
        replace_existing=True,    # agar shu id bilan vazifa allaqachon bo'lsa, uni yangisiga almashtiradi
    )
    scheduler.start()