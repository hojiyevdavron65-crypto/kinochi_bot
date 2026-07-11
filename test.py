"""
test.py — loyihaning asosiy qismlarini unittest orqali tekshiruvchi skript.

Nima uchun TestCase: har bir test alohida, mustaqil holatda ishlaydi,
bitta test xato bersa ham qolganlari davom etadi, va natija
standart, tushunarli formatda chiqadi.

Ishlatish: python test.py
yoki:      python -m unittest test.py -v
"""

import shutil
import unittest


class ConfigTestCase(unittest.TestCase):
    """.env orqali o'qilgan sozlamalar to'g'ri kelayotganini tekshiradi."""

    @classmethod
    def setUpClass(cls):
        from data.config import config
        cls.config = config

    def test_bot_token_exists(self):
        self.assertTrue(self.config.BOT_TOKEN, "BOT_TOKEN .env faylida yo'q yoki bo'sh")

    def test_database_credentials_exist(self):
        self.assertTrue(self.config.DB_HOST, "DB_HOST bo'sh")
        self.assertTrue(self.config.DB_USER, "DB_USER bo'sh")
        self.assertTrue(self.config.DB_PASSWORD, "DB_PASSWORD bo'sh")
        self.assertTrue(self.config.DB_NAME, "DB_NAME bo'sh")

    def test_admins_list_parsed_correctly(self):
        # ADMINS satr emas, balki int'lardan iborat list bo'lishi kerak
        self.assertIsInstance(self.config.ADMINS, list)
        if self.config.ADMINS:
            self.assertIsInstance(self.config.ADMINS[0], int)


class DatabaseConnectionTestCase(unittest.IsolatedAsyncioTestCase):
    """PostgreSQL bilan ulanish va jadvallar yaratilishini tekshiradi."""

    async def asyncSetUp(self):
        from data.database import db
        self.db = db
        await self.db.create_pool()

    async def asyncTearDown(self):
        await self.db.close_pool()

    async def test_connection_pool_created(self):
        self.assertIsNotNone(self.db.pool, "Connection pool yaratilmadi")

    async def test_tables_created_without_error(self):
        # Xato chiqmasligi kifoya — jadval allaqachon bo'lsa ham qayta yaratishga urinmaydi
        try:
            await self.db.create_tables()
        except Exception as e:
            self.fail(f"Jadval yaratishda xatolik: {e}")


class MoviesCrudTestCase(unittest.IsolatedAsyncioTestCase):
    """Kinolar bilan bog'liq CRUD funksiyalarni (add/get/delete) tekshiradi."""

    TEST_CODE = "__test_code_123__"

    async def asyncSetUp(self):
        from data.database import db
        from data.db_commands import add_movie, delete_movie

        self.add_movie = add_movie
        self.delete_movie = delete_movie

        await db.create_pool()

        # Har ehtimolga qarshi — oldingi testdan qolgan bo'lishi mumkin bo'lgan yozuvni tozalaymiz
        await self.delete_movie(self.TEST_CODE)

        await self.add_movie(
            code=self.TEST_CODE,
            title="Test Kino",
            file_id="test_file_id",
            file_type="video",
            added_by=123456789,
        )

    async def asyncTearDown(self):
        from data.database import db
        # Test tugagach, qoldirilgan test yozuvini albatta o'chiramiz
        await self.delete_movie(self.TEST_CODE)
        await db.close_pool()

    async def test_code_exists_after_adding(self):
        from data.db_commands import check_code_exists
        exists = await check_code_exists(self.TEST_CODE)
        self.assertTrue(exists, "Qo'shilgan kino kodi mavjud deb topilmadi")

    async def test_movie_data_matches(self):
        from data.db_commands import get_movie_by_code
        movie = await get_movie_by_code(self.TEST_CODE)
        self.assertIsNotNone(movie)
        self.assertEqual(movie["title"], "Test Kino")
        self.assertEqual(movie["file_type"], "video")

    async def test_movie_deletion(self):
        from data.db_commands import check_code_exists
        await self.delete_movie(self.TEST_CODE)
        exists = await check_code_exists(self.TEST_CODE)
        self.assertFalse(exists, "Kino o'chirilgandan keyin ham mavjud bo'lib qolyapti")


class UsersCrudTestCase(unittest.IsolatedAsyncioTestCase):
    """Foydalanuvchilar bilan bog'liq CRUD funksiyalarni tekshiradi."""

    TEST_USER_ID = 999999999  # haqiqiy foydalanuvchi bilan to'qnashmasligi uchun katta son

    async def asyncSetUp(self):
        from data.database import db
        from data.db_commands import add_user

        await db.create_pool()
        await add_user(self.TEST_USER_ID, username="test_user", full_name="Test User")

    async def asyncTearDown(self):
        from data.database import db
        await db.close_pool()

    async def test_user_exists_after_adding(self):
        from data.db_commands import check_user_exists
        exists = await check_user_exists(self.TEST_USER_ID)
        self.assertTrue(exists, "Qo'shilgan foydalanuvchi mavjud deb topilmadi")

    async def test_duplicate_add_does_not_fail(self):
        # ON CONFLICT DO NOTHING to'g'ri ishlayotganini tekshiramiz —
        # bir xil user_id ikkinchi marta qo'shilsa, xato chiqmasligi kerak
        from data.db_commands import add_user
        try:
            await add_user(self.TEST_USER_ID, username="test_user", full_name="Test User")
        except Exception as e:
            self.fail(f"Dublikat foydalanuvchi qo'shishda xatolik: {e}")


class RequiredChannelsCrudTestCase(unittest.IsolatedAsyncioTestCase):
    """Majburiy obuna kanallari bilan bog'liq CRUD funksiyalarni tekshiradi."""

    TEST_CHANNEL_ID = -1009999999999

    async def asyncSetUp(self):
        from data.database import db
        from data.db_commands import add_required_channel, delete_required_channel

        self.delete_required_channel = delete_required_channel

        await db.create_pool()
        await delete_required_channel(self.TEST_CHANNEL_ID)  # oldingi qoldiqni tozalash
        await add_required_channel(self.TEST_CHANNEL_ID, username="test_channel", name="Test Kanal")

    async def asyncTearDown(self):
        from data.database import db
        await self.delete_required_channel(self.TEST_CHANNEL_ID)
        await db.close_pool()

    async def test_channel_appears_in_list(self):
        from data.db_commands import get_required_channels
        channels = await get_required_channels()
        found = any(ch["channel_id"] == self.TEST_CHANNEL_ID for ch in channels)
        self.assertTrue(found, "Qo'shilgan kanal ro'yxatda topilmadi")


class VideoUtilsTestCase(unittest.TestCase):
    """ffmpeg/ffprobe tizimda mavjudligini tekshiradi (deploy'dan keyin muhim)."""

    def test_ffmpeg_available(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest(
                "ffmpeg/ffprobe hozircha o'rnatilmagan — serverga deploy qilgandan "
                "keyin o'rnatiladi, lokal test uchun bu majburiy emas."
            )


class ImportsTestCase(unittest.TestCase):
    """Barcha muhim modullar xatosiz import qilinishini tekshiradi."""

    def test_middleware_imports(self):
        try:
            from middlewares import ThrottlingMiddleware
            ThrottlingMiddleware(limit=1.0)
        except Exception as e:
            self.fail(f"Middleware import xatoligi: {e}")

    def test_handlers_import(self):
        try:
            from handlers import router  # noqa: F401
        except Exception as e:
            self.fail(f"Handlerlarni import qilishda xatolik: {e}")

    def test_keyboards_import(self):
        try:
            from keyboards.inline_keyboards import get_movie_deeplink_keyboard  # noqa: F401
        except Exception as e:
            self.fail(f"Keyboards import xatoligi: {e}")

    def test_filters_import(self):
        try:
            from filters import IsAdmin, IsSubscribed  # noqa: F401
        except Exception as e:
            self.fail(f"Filters import xatoligi: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)