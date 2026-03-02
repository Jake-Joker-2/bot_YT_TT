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

DOWNLOAD_DIR = "/tmp/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Отправь ссылку на TikTok, YouTube нету так как он пидорас\n"
        "⚠️ Лимит: видео до 50 МБ"
    )


def download_video(url: str) -> str:
    ydl_opts = {
        'format': 'best[filesize<50M]',
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['web'],
                'player_skip': ['webpage', 'configs', 'js'],
                'po_token': ['JgZ51IXv4NGXqs19/AHwYhiZPuoEDJyK6R'],
            }
        },
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("❌ Это не ссылка. Отправь URL")
        return
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_video")
    status_message = await update.message.reply_text("⏳ Скачиваю видео...")
    
    try:
        loop = asyncio.get_event_loop()
        filepath = await loop.run_in_executor(None, download_video, url)
        
        if not os.path.exists(filepath):
            await status_message.edit_text("❌ Файл не найден после скачивания")
            return
        
        with open(filepath, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption="✅ Готово!"
            )
        
        os.remove(filepath)
        await status_message.delete()
        
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await status_message.edit_text(f"❌ Ошибка:\n<code>{str(e)}</code>", parse_mode='HTML')


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    
    print("🚀 Бот запущен!")
    application.run_polling()


if __name__ == "__main__":
    main()