import os
import shutil
import subprocess

from aiogram import Bot

TEMP_DIR = "temp"


async def download_telegram_file(bot: Bot, file_id: str) -> str:
    """
    Local Bot API Server orqali faylni oladi.

    Oddiy Bot API'da faylni HTTP orqali yuklab olish kerak edi (20 MB cheklov bilan).
    Local server rejimida esa fayl allaqachon diskda turadi — bot.get_file()
    qaytargan `file_path` to'g'ridan-to'g'ri lokal manzil, shuning uchun
    shunchaki bizning ishchi papkamizga nusxalaymiz.
    """
    os.makedirs(TEMP_DIR, exist_ok=True)

    file = await bot.get_file(file_id)

    # Local mode'da file.file_path — bu konteyner ichidagi haqiqiy fayl manzili
    local_path = os.path.join(TEMP_DIR, f"{file_id}.mp4")
    shutil.copy(file.file_path, local_path)

    return local_path


def get_video_duration(filepath: str) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            filepath,
        ],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def extract_preview_clip(filepath: str, duration: int = 30) -> str:
    total_duration = get_video_duration(filepath)
    start_time = total_duration * 0.4
    if start_time + duration > total_duration:
        start_time = max(total_duration - duration, 0)

    output_path = filepath.replace(".mp4", "_preview.mp4")

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-ss", str(start_time),
            "-i", filepath,
            "-t", str(duration),
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-c:a", "aac",
            output_path,
        ],
        check=True,
        capture_output=True,
    )
    return output_path


def cleanup_files(*paths: str) -> None:
    for path in paths:
        if path and os.path.exists(path):
            os.remove(path)