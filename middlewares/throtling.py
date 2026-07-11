from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message
from cachetools import TTLCache


class ThrottlingMiddleware(BaseMiddleware):
    """
    Foydalanuvchi juda tez-tez xabar yuborishining (spam/flood) oldini oladigan middleware.

    Qanday ishlaydi:
    - Har bir foydalanuvchi uchun "keshda" bitta belgi saqlanadi.
    - Agar foydalanuvchi belgilangan vaqt ichida (masalan 1 soniya) yana xabar yuborsa,
      bu xabar handler'ga yuborilmaydi — shu yerda to'xtatiladi.
    - Vaqt o'tgach (TTL tugagach), foydalanuvchi kesh'dan avtomatik o'chadi
      va yana xabar yubora oladi.

    Nega TTLCache ishlatilgan:
    - Oddiy dictionary ishlatsak, vaqt o'tishi bilan foydalanuvchilar sonini
      qo'lda tozalashimiz kerak bo'lardi (memory leak xavfi).
    - TTLCache esa muddati o'tgan yozuvlarni o'zi avtomatik o'chirib turadi.
    """

    def __init__(self, limit: float = 1.0):
        """
        :param limit: bitta foydalanuvchi ikkita xabar orasida kutishi kerak bo'lgan
                       minimal vaqt (soniyalarda). Default: 1 soniya.
        """
        # maxsize — kesh ichida bir vaqtning o'zida necha foydalanuvchi saqlanishi mumkinligi
        # ttl — har bir yozuv necha soniyadan keyin o'zi o'chib ketishi (limit bilan bir xil)
        self.cache = TTLCache(maxsize=10_000, ttl=limit)

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id

        # Agar bu foydalanuvchi kesh ichida allaqachon bo'lsa —
        # demak u limit vaqti ichida qayta xabar yubordi, ya'ni SPAM qilyapti.
        if user_id in self.cache:
            # Handler'ga umuman kirmaymiz — xabar shu yerda "yutiladi".
            # Xohlasa, foydalanuvchiga ogohlantirish xabari yuborish ham mumkin,
            # lekin har safar ogohlantirish yuborish o'zi ham spam bo'lib ketishi mumkin,
            # shuning uchun jim tarzda e'tiborsiz qoldiramiz.
            return

        # Foydalanuvchini keshga qo'shamiz — endi u `limit` soniya davomida
        # yangi xabar yubora olmaydi (yuborsa, yuqoridagi shart uni to'xtatadi).
        self.cache[user_id] = True

        # Hammasi joyida — xabarni asl handler'ga (masalan search_movie) o'tkazamiz.
        return await handler(event, data)