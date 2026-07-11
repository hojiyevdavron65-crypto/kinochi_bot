from aiogram import Router

from handlers.admins import admin_router
from handlers.channels import channel_router
from handlers.users import user_router

router = Router()

# TARTIB MUHIM!
# Admin va kanal boshqaruv routerlari birinchi ulanishi kerak,
# aks holda admin yozgan har qanday matn user_router tomonidan
# "kino kodi" deb qabul qilinib ketishi mumkin.
router.include_router(admin_router)
router.include_router(channel_router)
router.include_router(user_router)

__all__ = ["router"]