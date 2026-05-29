"""
CaptionAPI Telegram Bot
Users send images -> get captions
Free tier: 10/day
Premium: unlimited via subscription
"""

import asyncio, logging, os, io, hashlib, base64, time
from datetime import datetime, timedelta
from collections import defaultdict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# Config
TOKEN = "8150045080:AAHLSOH0WsHnW2fRKoLmLyF_Q-7v9TbYeGk"
RAILWAY_API = "https://caption-api-production-7b73.up.railway.app"
FREE_LIMIT = 10  # free captions per day
PREMIUM_PRICE = 5  # USD (плата через звезды Telegram / crypto)

# User tracking
user_usage = defaultdict(lambda: {"date": "", "count": 0})

logging.basicConfig(level=logging.INFO)

def get_usage(user_id: int) -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    u = user_usage[user_id]
    if u["date"] != today:
        u["date"] = today
        u["count"] = 0
    return u["count"]

def increment_usage(user_id: int):
    u = user_usage[user_id]
    if u["date"] != datetime.now().strftime("%Y-%m-%d"):
        u["date"] = datetime.now().strftime("%Y-%m-%d")
        u["count"] = 0
    u["count"] += 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    usage = get_usage(u.id)
    remaining = max(0, FREE_LIMIT - usage)
    
    text = (
        f"👋 Привет, {u.first_name}!\n\n"
        f"Я CaptionAPI бот. Отправь мне изображение, и я сгенерирую "
        f"качественное описание (кэпшен) для AI датасетов.\n\n"
        f"📊 Лимит: {remaining}/{FREE_LIMIT} бесплатно в день\n"
        f"🚀 Премиум: безлимит — {PREMIUM_PRICE}$\n\n"
        f"Поддерживаются: PNG, JPG, JPEG, WEBP, GIF"
    )
    
    keyboard = [
        [InlineKeyboardButton("⭐ Премиум", callback_data="premium")],
        [InlineKeyboardButton("📖 API документация", url=f"{RAILWAY_API}/docs")],
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def premium_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        f"⭐ Премиум CaptionAPI ⭐\n\n"
        f"✅ Безлимитные кэпшены\n"
        f"✅ AI-кэпшенинг (Moondream)\n"
        f"✅ Приоритетная обработка\n"
        f"✅ Пакетная загрузка (до 10)\n\n"
        f"💰 Цена: {PREMIUM_PRICE}$ / месяц\n\n"
        f"Оплата через Telegram Stars ⭐"
    )
    await query.edit_message_text(text)

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    usage = get_usage(u.id)
    
    if usage >= FREE_LIMIT:
        keyboard = [[InlineKeyboardButton("⭐ Купить премиум", callback_data="premium")]]
        await update.message.reply_text(
            "😔 Лимит на сегодня исчерпан (10/10).\n"
            "Купи премиум для безлимита!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    msg = await update.message.reply_text("🔄 Обрабатываю изображение...")
    
    try:
        # Download image
        file = await update.message.effective_attachment[-1].get_file()
        image_bytes = await file.download_as_bytearray()
        
        # Call our API
        import httpx
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{RAILWAY_API}/caption",
                files={"file": (file.file_path.split("/")[-1] or "image.png", 
                               io.BytesIO(bytes(image_bytes)), "image/png")}
            )
        
        if resp.status_code != 200:
            await msg.edit_text(f"❌ Ошибка API: {resp.status_code}")
            return
        
        data = resp.json()
        caption = data["caption"]
        tags = ", ".join(data["tags"]) if data["tags"] else "—"
        model = data["model_used"]
        
        increment_usage(u.id)
        remaining = FREE_LIMIT - get_usage(u.id)
        
        text = (
            f"📝 **Кэпшен:**\n{caption}\n\n"
            f"🏷️ **Теги:** {tags}\n"
            f"🤖 **Модель:** {model}\n"
            f"🎯 **Уверенность:** {data['confidence']*100:.0f}%\n\n"
            f"📊 Осталось: {remaining}/{FREE_LIMIT}"
        )
        
        await msg.edit_text(text)
        
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {str(e)[:200]}")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 **Команды:**\n"
        "/start — Приветствие\n"
        "/help — Эта справка\n"
        "/status — Мой статус\n"
        "/premium — Премиум\n\n"
        "📤 **Использование:**\n"
        "Просто отправь фото!"
    )
    await update.message.reply_text(text)

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    usage = get_usage(u.id)
    remaining = max(0, FREE_LIMIT - usage)
    
    text = (
        f"📊 **Статус**\n\n"
        f"👤 {u.first_name}\n"
        f"🆔 {u.id}\n"
        f"📊 Использовано: {usage}/{FREE_LIMIT} сегодня\n"
        f"✅ Осталось: {remaining}\n"
        f"💎 Статус: Бесплатно"
    )
    await update.message.reply_text(text)

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("premium", premium_info))
    app.add_handler(CallbackQueryHandler(premium_info, pattern="premium"))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    
    print("Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
