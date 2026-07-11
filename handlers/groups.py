from aiogram.filters import Command,CommandObject,IS_ADMIN
from aiogram.types import Message
import asyncio
from aiogram import types
from aiogram import F,Router,Bot
from aiogram.types import BufferedInputFile
from filters.filters import IsAdminFilter

group_router=Router()

group_router.message.filter(F.chat.type.in_({"group","supergroup"}))

#Guruh nomini O'zgartirish uchun
@group_router.message(Command("settitle"),IsAdminFilter())
async def set_title(message: types.Message,command:CommandObject):
    if not command.args:
        return await message.answer("Guruh nomini o'zgartirish uchun /settitle guruh nomi ni yuboring")
    await message.chat.set_title(command.args)
    await message.answer("Guruh nomi muvaffaqiyatli o'zgartirildi")


#Guruh desciriptionni o'zgartirish uchun
@group_router.message(Command("set_description"),IsAdminFilter())
async def set_description(message: types.Message,command:CommandObject):
    if not command.args:
        return await message.answer("Guruhning descriptionni o'zgartirish uchun /set_description guruh description ni yuboring")
    await message.chat.set_description(command.args)
    await message.answer("Guruh descriptionni muvaffaqiyatli o'zgartirildi")



#Guruhga yangi qo'shilmoqchi bo'lganda
@group_router.message(F.new_chat_member)
async def new_member(message: types.Message):
    await message.reply(f"Xush kelibsiz {message.from_user.username}")


#Guruhdan chiqarish uchun
@group_router.message(Command("ban"),IsAdminFilter())
async def ban(message: types.Message):
    if not message.reply_to_message:
        return await message.answer("Kimni chiqaramiz ayting menga /ban reply qilib yuboring")
    await message.chat.ban(message.reply_to_message.from_user.id)
    await message.answer("Chopdim guruhdan")
    await message.delete()

#guruhdagi photo rasmini o'zgartirish uchun
@group_router.message(Command("setphoto"),IsAdminFilter())
async def set_photo_group(message:types.Message,bot:Bot):
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await message.answer("Rasmga reply qilib /setphoto deb yuboring")


    photo=message.reply_to_message.photo[-1]
    file=await bot.get_file(photo.file_id)
    content=await bot.download_file(file.file_path)
    photo_file=BufferedInputFile(content.read(),filename="group.jpg")


    await message.chat.set_photo(photo=photo_file)
    await message.answer("Guruh rasmi o'zgartirildi")