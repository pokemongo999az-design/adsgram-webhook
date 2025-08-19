import telebot
from telebot import types
from PIL import Image, ImageDraw, ImageFont
import os

# === CONFIG ===
API_TOKEN = "8230805944:AAEpj5ZC2ZRokTkmwcBbXps5_VTOvftuhoY"
BACKGROUND_IMAGE = "background_game.png"  # ton image de base
FONT_PATH = "arial.ttf"  # Mets ici la police que tu veux utiliser
OUTPUT_IMAGE = "game_screen.png"

REWARD_PER_AD = 0.000181818182

bot = telebot.TeleBot(API_TOKEN)

# stockage utilisateurs
user_data = {}

# === Générateur d’image ===
def generate_game_image(user_id):
    total = user_data.get(user_id, 0.0)

    # Ouvre le fond
    img = Image.open(BACKGROUND_IMAGE).convert("RGBA")
    draw = ImageDraw.Draw(img)

    # Police
    font = ImageFont.truetype(FONT_PATH, 60)

    # Texte solde TON
    text = f"{total:.8f} TON"
    tw, th = draw.textbbox((0, 0), text, font=font)[2:]
    x = (img.width - tw) // 2
    y = img.height - th - 50
    draw.text((x-2, y-2), text, font=font, fill="black")
    draw.text((x+2, y-2), text, font=font, fill="black")
    draw.text((x-2, y+2), text, font=font, fill="black")
    draw.text((x+2, y+2), text, font=font, fill="black")
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

# === Callback pub ===
@bot.callback_query_handler(func=lambda call: call.data == "watch_ad")
def callback_watch_ad(call):
    user_id = call.from_user.id
    user_data[user_id] = user_data.get(user_id, 0.0) + REWARD_PER_AD
    bot.answer_callback_query(call.id, "✅ Pub vue ! Récompense ajoutée.")
    send_game_screen(call.message.chat.id, user_id)

# === Callback solde ===
@bot.callback_query_handler(func=lambda call: call.data == "balance")
def callback_balance(call):
    user_id = call.from_user.id
    bot.answer_callback_query(call.id)
    send_game_screen(call.message.chat.id, user_id)

# === Callback retrait ===
@bot.callback_query_handler(func=lambda call: call.data == "withdraw")
def callback_withdraw(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "💸 Fonction de retrait en cours de développement...")

# === Fonction envoi écran de jeu ===
def send_game_screen(chat_id, user_id):
    path = generate_game_image(user_id)
    with open(path, "rb") as img:
        bot.send_photo(chat_id, img, caption=f"💰 Solde actuel : {user_data[user_id]:.8f} TON", reply_markup=main_menu())

# === Lancement ===
print("✅ Bot de minage TON démarré...")
bot.polling(none_stop=True)
