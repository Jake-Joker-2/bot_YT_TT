import logging
import os
import asyncio
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = "8786785691:AAFQ1ATab63nJKcXxyPyIKuFJy7Hw119WV0"

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
 
    await update.message.reply_text(
        "👋 Привет! Отправь мне ссылку на YouTube или TikTok, и я скачаю видео.\n\n"
        "⚠️ Пока работаю с видео до 50 МБ (лимит Telegram)"
    )


def download_video_sync(url: str) -> str:
    ydl_opts = {
        'format': 'best[filesize<50M]',
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not (url.startswith('http://') or url.startswith('https://')):
        await update.message.reply_text("❌ Это не похоже на ссылку. Отправь URL на YouTube или TikTok")
        return

    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_video")
    status_message = await update.message.reply_text("⏳ Скачиваю видео, подожди...")
    
    try:
        loop = asyncio.get_event_loop()
        filepath = await loop.run_in_executor(None, download_video_sync, url)
        
        if not os.path.exists(filepath):
            await status_message.edit_text("❌ Файл не найден после скачивания")
            return
        
        with open(filepath, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption="✅ Готово! Вот твоё видео"
            )
        
        os.remove(filepath)
        await status_message.delete()
        
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await status_message.edit_text(
            f"❌ Ошибка при скачивании:\n<code>{str(e)}</code>",
            parse_mode='HTML'
        )


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    
    print("🚀 Бот запущен! Нажми Ctrl+C для остановки")
    application.run_polling()


if __name__ == "__main__":
    main()