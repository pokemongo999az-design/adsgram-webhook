import telebot
from telebot import types
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, request
import os

# === CONFIG ===
API_TOKEN = os.getenv("BOT_TOKEN", "TON_TOKEN_ICI")  # sécurise via Render Env Vars
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://ton-app.onrender.com")  # mets ton URL Render
BACKGROUND_IMAGE = "background_game.png"
FONT_PATH = "arial.ttf"
OUTPUT_IMAGE = "game_screen.png"

REWARD_PER_AD = 0.000181818182

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# stockage utilisateurs
user_data = {}

# === Générateur d’image ===
def generate_game_image(user_id):
    total = user_data.get(user_id, 0.0)
    img = Image.open(BACKGROUND_IMAGE).convert("RGBA")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, 60)
    text = f"{total:.8f} TON"
    tw, th = draw.textbbox((0, 0), text, font=font)[2:]
    x = (img.width - tw) // 2
    y = img.height - th - 50
    for dx, dy in [(-2,-2),(2,-2),(-2,2),(2,2)]:
        draw.text((x+dx, y+dy), text, font=font, fill="black")
    draw.text((x, y), text, font=font, fill="white")
    img.save(OUTPUT_IMAGE)
    return OUTPUT_IMAGE

# === Générateur de menu ===
def main_menu():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("📺 Miner", callback_data="watch_ad")
    btn2 = types.InlineKeyboardButton("💰 Solde", callback_data="balance")
    btn3 = types.InlineKeyboardButton("💸 Retrait", callback_data="withdraw")
    markup.add(btn1)
    markup.add(btn2, btn3)
    return markup

# === Commande /start ===
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = 0.0
    bot.send_message(message.chat.id, "👋 Bienvenue dans le mineur TON !", reply_markup=main_menu())
    send_game_screen(message.chat.id, user_id)

# === Callbacks ===
@bot.callback_query_handler(func=lambda call: call.data == "watch_ad")
def callback_watch_ad(call):
    user_id = call.from_user.id
    user_data[user_id] = user_data.get(user_id, 0.0) + REWARD_PER_AD
    bot.answer_callback_query(call.id, "✅ Pub vue ! Récompense ajoutée.")
    send_game_screen(call.message.chat.id, user_id)

@bot.callback_query_handler(func=lambda call: call.data == "balance")
def callback_balance(call):
    user_id = call.from_user.id
    bot.answer_callback_query(call.id)
    send_game_screen(call.message.chat.id, user_id)

@bot.callback_query_handler(func=lambda call: call.data == "withdraw")
def callback_withdraw(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "💸 Fonction de retrait en cours de développement...")

# === Fonction envoi écran de jeu ===
def send_game_screen(chat_id, user_id):
    path = generate_game_image(user_id)
    with open(path, "rb") as img:
        bot.send_photo(chat_id, img, caption=f"💰 Solde actuel : {user_data[user_id]:.8f} TON", reply_markup=main_menu())

# === Flask webhook routes ===
@app.route("/", methods=["GET"])
def index():
    return "Bot en ligne 🚀"

@app.route("/", methods=["POST"])
def webhook():
    json_str = request.stream.read().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

# === Lancement ===
if __name__ == "__main__":
    # Définir webhook à chaque redémarrage
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
