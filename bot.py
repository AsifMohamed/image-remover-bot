import os
import gspread
import os
import json
from oauth2client.service_account import ServiceAccountCredentials
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

from rembg import remove, new_session
from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters

# =========================
# BOT TOKEN
# =========================
TOKEN = "8865876151:AAEZnT8S6AScW4TvcySj7PAfMZwQnM6jf38"

# =========================
# GOOGLE SHEETS SETUP
# =========================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = json.loads(os.environ["CREDS_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

client = gspread.authorize(creds)

sheet = client.open("BGRemoverUserlogs").sheet1

# =========================
# FOLDERS
# =========================
os.makedirs("input", exist_ok=True)
os.makedirs("output", exist_ok=True)
session = new_session("u2netp")

# =========================
# LOG FUNCTION
# =========================
def log_user(user_id, username, action):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sheet.append_row([
        str(user_id),
        username if username else "unknown",
        action,
        now
    ])


# =========================
# START COMMAND
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    log_user(user.id, user.username, "start")

    await update.message.reply_text(
        "👋 Send me a photo and I'll remove its background."
    )


# =========================
# PHOTO HANDLER
# =========================
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user
    log_user(user.id, user.username, "photo_received")

    await update.message.reply_text("⏳ Removing background...")

    photo = update.message.photo[-1]

    input_path = f"input/{photo.file_unique_id}.jpg"
    output_path = f"output/{photo.file_unique_id}.png"

    file = await context.bot.get_file(photo.file_id)
    await file.download_to_drive(input_path)

    with open(input_path, "rb") as i:
        input_data = i.read()

    output_data = remove(input_data, session=session)

    with open(output_path, "wb") as o:
        o.write(output_data)

    with open(output_path, "rb") as image:
        await update.message.reply_document(
            document=image,
            filename="background_removed.png"
        )

    log_user(user.id, user.username, "photo_processed")

    os.remove(input_path)
    os.remove(output_path)


# =========================
# APP SETUP
# =========================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

print("🤖 AI Background Remover Bot Running...")

app.run_polling()
