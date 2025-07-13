import json
import os
import threading
import time
from datetime import datetime
import pytz
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === Cấu hình ===
BOT_TOKEN = "7806552255:AAF0grPJ2p6a9haqzFgNacRNrXt-1ZipXv4"  # 🔁 Thay bằng token của bạn
JSON_FILE = 'reminders.json'
TIMEZONE = pytz.timezone('Asia/Ho_Chi_Minh')


# === Xử lý JSON ===
def load_data():
    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False)
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def generate_id(data):
    return max([item["id"] for item in data], default=0) + 1


# === Các lệnh bot ===
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Chào bạn! Đây là bot nhắc thanh toán.\n\n"
        "• /add [ngày] [nội dung] – thêm lời nhắc lặp lại hằng tháng\n"
        "• /list – xem danh sách lời nhắc\n"
        "• /remove [id] – xóa lời nhắc theo ID"
    )

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Sai cú pháp. Dùng: /add [ngày] [nội dung]")
        return

    try:
        day = int(context.args[0])
        if not 1 <= day <= 31:
            await update.message.reply_text("Ngày phải từ 1 đến 31.")
            return
    except ValueError:
        await update.message.reply_text("Ngày phải là số nguyên.")
        return

    text = ' '.join(context.args[1:]).strip()
    if not text:
        await update.message.reply_text("Vui lòng nhập nội dung lời nhắc.")
        return

    data = load_data()
    new_item = {
        "id": generate_id(data),
        "user_id": update.effective_user.id,
        "day": day,
        "text": text
    }
    data.append(new_item)
    save_data(data)
    await update.message.reply_text(f"✅ Đã thêm lời nhắc: \"{text}\" vào ngày {day} hàng tháng. ID: {new_item['id']}")

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user_id = update.effective_user.id
    reminders = [r for r in data if r["user_id"] == user_id]
    if not reminders:
        await update.message.reply_text("📭 Bạn chưa có lời nhắc nào.")
    else:
        msg = "📋 Danh sách lời nhắc:\n"
        for r in reminders:
            msg += f"🔸 ID {r['id']} – Ngày {r['day']} – \"{r['text']}\"\n"
        await update.message.reply_text(msg)

async def remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("Sai cú pháp. Dùng: /remove [id]")
        return

    rid = int(context.args[0])
    data = load_data()
    user_id = update.effective_user.id
    new_data = [r for r in data if not (r['id'] == rid and r['user_id'] == user_id)]

    if len(new_data) == len(data):
        await update.message.reply_text("Không tìm thấy ID phù hợp.")
    else:
        save_data(new_data)
        await update.message.reply_text(f"🗑️ Đã xóa lời nhắc có ID {rid}.")


# === Tự động gửi nhắc mỗi sáng ===
async def check_reminders(app):
    while True:
        now = datetime.now(TIMEZONE)
        if now.hour == 8 and now.minute == 0:
            data = load_data()
            for item in data:
                uid = item['user_id']
                text = item['text']
                remind_day = item['day']
                delta = remind_day - now.day
                msg = None
                if delta == 0:
                    msg = f"🚨 Gấp! Hôm nay là ngày thanh toán: {text}"
                elif delta == -1:
                    msg = f"⏰ Còn 1 ngày đến ngày thanh toán: {text}"
                elif delta == -2:
                    msg = f"⏰ Còn 2 ngày đến ngày thanh toán: {text}"
                if msg:
                    try:
                        await app.bot.send_message(chat_id=uid, text=msg)
                    except:
                        pass
        time.sleep(60)


def start_scheduler(app):
    thread = threading.Thread(target=lambda: app.create_task(check_reminders(app)))
    thread.daemon = True
    thread.start()


# === Chạy bot ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("add", add_command))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("remove", remove_command))

    start_scheduler(app)

    print("🤖 Bot đang chạy...")
    app.run_polling()
