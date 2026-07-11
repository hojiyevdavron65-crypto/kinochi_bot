import os
import subprocess

from aiogram import Bot

# Vaqtinchalik fayllar shu papkada saqlanadi (video yuklab olinganda, preview kesilganda)
TEMP_DIR = "temp"


async def download_telegram_file(bot: Bot, file_id: str) -> str:
    """
    Telegram serveridan faylni (file_id orqali) diskka yuklab oladi.

    Nega kerak: Telegram file_id orqali faylni to'g'ridan-to'g'ri ffmpeg bilan
    qayta ishlab bo'lmaydi — avval uni diskka jismoniy fayl sifatida saqlash kerak.

    :param bot: aiogram Bot obyekti (Telegram API bilan aloqa qilish uchun)
    :param file_id: Telegram fayl identifikatori
    :return: yuklab olingan faylning lokal manzili (path)
    """
    os.makedirs(TEMP_DIR, exist_ok=True)

    # Telegram'dan faylning serverdagi manzilini so'raymiz
    file = await bot.get_file(file_id)

    # Faylni shu file_id nomi bilan lokal saqlaymiz (unikal nom bo'lishi uchun)
    local_path = os.path.join(TEMP_DIR, f"{file_id}.mp4")
    await bot.download_file(file.file_path, destination=local_path)

    return local_path


def get_video_duration(filepath: str) -> float:
    """
    ffprobe yordamida video faylning umumiy davomiyligini (soniyalarda) aniqlaydi.

    Nega kerak: preview klipni to'g'ri joydan kesish uchun avval
    filmning umumiy uzunligini bilishimiz shart.
    """
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",                                  # faqat xatolarni chiqar, ortiqcha log kerak emas
            "-show_entries", "format=duration",               # bizga faqat davomiylik kerak
            "-of", "default=noprint_wrappers=1:nokey=1",      # natijani sof raqam qilib qaytar
            filepath,
        ],
        capture_output=True,
        text=True,
        check=True,  # xato bo'lsa, subprocess.CalledProcessError ko'tariladi
    )
    return float(result.stdout.strip())


def extract_preview_clip(filepath: str, duration: int = 30) -> str:
    """
    Filmning eng "qiziq" joyidan qisqa preview klip kesib oladi.

    Mantiq: filmning boshi (kirish qismi) yoki oxiri (final) odatda unchalik
    qiziqarli bo'lmaydi. Shuning uchun umumiy uzunlikning 40%-45% qismidan
    boshlab kesamiz — bu odatda syujet allaqachon qizigan payt bo'ladi.

    :param filepath: asl (to'liq) video faylning manzili
    :param duration: kesib olinadigan klipning uzunligi (soniyalarda)
    :return: kesilgan preview faylning manzili
    """
    total_duration = get_video_duration(filepath)

    # Klip boshlanish nuqtasi — filmning 40%-lik joyi
    start_time = total_duration * 0.4

    # Agar shu nuqtadan boshlab kesilgan klip video oxiridan oshib ketsa
    # (masalan, film juda qisqa bo'lsa), boshlanish nuqtasini orqaga suramiz —
    # shunda klip doim video ichida to'liq sig'adi.
    if start_time + duration > total_duration:
        start_time = max(total_duration - duration, 0)

    # Chiqish fayli nomi — asl fayl nomiga "_preview" qo'shib yasaymiz
    output_path = filepath.replace(".mp4", "_preview.mp4")

    subprocess.run(
        [
            "ffmpeg",
            "-y",                          # chiqish fayli mavjud bo'lsa, so'ramasdan ustidan yoz
            "-ss", str(start_time),        # qaysi soniyadan boshlab kesish kerak
            "-i", filepath,                # asl video fayl
            "-t", str(duration),           # necha soniyalik klip kerak
            "-c:v", "libx264",             # video kodek — keng qo'llab-quvvatlanadi (Telegram, Instagram)
            "-preset", "veryfast",         # tezroq kodlash, sifatdan unchalik yutqazmaydi
            "-c:a", "aac",                  # audio kodek
            output_path,
        ],
        check=True,
        capture_output=True,  # ffmpeg'ning konsolga chiqargan ortiqcha loglarini yashiradi
    )

    return output_path


def cleanup_files(*paths: str) -> None:
    """
    Berilgan fayllarni diskdan o'chiradi (agar mavjud bo'lsa).

    Nega kerak: har bir kino qo'shilganda diskda vaqtinchalik fayllar
    (asl video, preview) qoladi. Agar ularni o'chirib turmasak,
    server diski asta-sekin to'lib qolishi mumkin.

    Bir nechta faylni bir vaqtda o'chirish uchun ishlatiladi:
    cleanup_files(original_path, preview_path)
    """
    for path in paths:
        if path and os.path.exists(path):
            os.remove(path)
