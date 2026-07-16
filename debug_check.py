from pyrogram import Client, filters
from data.config import config

app = Client("migrate_userbot", api_id=config.TELEGRAM_API_ID, api_hash=config.TELEGRAM_API_HASH)


@app.on_message(filters.text)
async def any_message(client, message):
    chat = message.chat
    print(f"📨 XABAR KELDI — chat.id={chat.id}, chat.username={chat.username}, text={message.text}")


print("✅ Userbot ishga tushmoqda... Eski botga QO'LDA '1' deb yozing (jarayon davomida istalgan vaqt).")
app.run()
