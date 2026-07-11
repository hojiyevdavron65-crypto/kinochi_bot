from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from data.db_commands import add_required_channel, get_required_channels, delete_required_channel
from filters.filters import IsAdmin

channel_router = Router()
channel_router.message.filter(IsAdmin())


class AddChannel(StatesGroup):
    waiting_for_channel = State()


class DeleteChannel(StatesGroup):
    waiting_for_channel_id = State()


# ==================== KANAL QO'SHISH ====================

@channel_router.message(Command("addchannel"))
async def cmd_add_channel(message: Message, state: FSMContext):
    await message.answer(
        "📢 Majburiy obuna uchun kanalni botga <b>forward</b> qiling "
        "(kanaldagi istalgan xabarni shu yerga forward qiling).\n\n"
        "⚠️ Bot o'sha kanalda <b>admin</b> bo'lishi shart, aks holda obunani tekshira olmaydi.\n\n"
        "Bekor qilish uchun /cancel",
        parse_mode="HTML",
    )
    await state.set_state(AddChannel.waiting_for_channel)


@channel_router.message(AddChannel.waiting_for_channel, F.forward_from_chat)
async def process_add_channel(message: Message, state: FSMContext):
    chat = message.forward_from_chat

    if chat.type != "channel":
        await message.answer("⚠️ Bu kanal emas. Iltimos, kanaldan xabar forward qiling.")
        return

    try:
        bot_member = await message.bot.get_chat_member(chat_id=chat.id, user_id=message.bot.id)
        if bot_member.status not in ("administrator", "creator"):
            await message.answer(
                "❌ Bot bu kanalda admin emas. Avval botni kanalga admin qilib qo'shing, "
                "keyin qayta urinib ko'ring."
            )
            return
    except Exception:
        await message.answer(
            "❌ Bot bu kanalga umuman a'zo emas. Avval botni kanalga admin qilib qo'shing."
        )
        return

    await add_required_channel(
        channel_id=chat.id,
        username=chat.username,
        name=chat.title,
    )

    await message.answer(
        f"✅ <b>{chat.title}</b> majburiy obuna ro'yxatiga qo'shildi!",
        parse_mode="HTML",
    )
    await state.clear()


@channel_router.message(AddChannel.waiting_for_channel)
async def process_wrong_channel_input(message: Message):
    await message.answer("⚠️ Iltimos, kanaldan xabarni forward qiling.")


# ==================== KANALLAR RO'YXATI ====================

@channel_router.message(Command("channels"))
async def cmd_list_channels(message: Message):
    channels = await get_required_channels()

    if not channels:
        await message.answer("📭 Hozircha majburiy obuna kanallari yo'q.")
        return

    text = "📢 <b>Majburiy obuna kanallari:</b>\n\n"
    for ch in channels:
        username_part = f"@{ch['channel_username']}" if ch["channel_username"] else "username yo'q"
        text += f"• {ch['channel_name']} ({username_part})\n  ID: <code>{ch['channel_id']}</code>\n\n"

    await message.answer(text, parse_mode="HTML")


# ==================== KANAL O'CHIRISH ====================

@channel_router.message(Command("delchannel"))
async def cmd_delete_channel(message: Message, state: FSMContext):
    channels = await get_required_channels()

    if not channels:
        await message.answer("📭 O'chirish uchun kanal yo'q.")
        return

    text = "🗑 O'chirmoqchi bo'lgan kanal ID sini kiriting:\n\n"
    for ch in channels:
        text += f"• {ch['channel_name']} — <code>{ch['channel_id']}</code>\n"

    await message.answer(text, parse_mode="HTML")
    await state.set_state(DeleteChannel.waiting_for_channel_id)


@channel_router.message(DeleteChannel.waiting_for_channel_id, F.text)
async def process_delete_channel(message: Message, state: FSMContext):
    try:
        channel_id = int(message.text.strip())
    except ValueError:
        await message.answer("⚠️ Noto'g'ri format. Faqat raqamli ID kiriting (masalan -1001234567890).")
        return

    await delete_required_channel(channel_id)
    await message.answer("✅ Kanal ro'yxatdan o'chirildi.")
    await state.clear()