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


BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден! Добавь его в переменные окружения Railway.")


DOWNLOAD_DIR = "/tmp/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Отправь ссылку на YouTube или TikTok.\n"
        "⚠️ Лимит: видео до 50 МБ"
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
        return ydl.prepare_filename(info)


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("❌ Отправь корректную ссылку")
        return
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_video")
    status = await update.message.reply_text("⏳ Скачиваю...")
    
    try:
        loop = asyncio.get_event_loop()
        filepath = await loop.run_in_executor(None, download_video_sync, url)
        
        if not os.path.exists(filepath):
            await status.edit_text("❌ Файл не найден")
            return
        
        with open(filepath, 'rb') as video:
            await update.message.reply_video(video=video, caption="✅ Готово!")
        
        os.remove(filepath)
        await status.delete()
        
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await status.edit_text(f"❌ Ошибка:\n<code>{str(e)}</code>", parse_mode='HTML')


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    
    print("🚀 Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()