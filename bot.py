import telebot
import json
import os
import html

# =========================================================
# BOT TOKEN
# =========================================================

TOKEN = "8309848913:AAF58_AXP3yWYzwSqWAQkjwyx8btNd4fo"

bot = telebot.TeleBot(
    TOKEN,
    parse_mode="HTML"
)

# =========================================================
# XOTIRA FAYLI
# =========================================================

FILE_NAME = "bot_xotirasi.json"


def load_data():
    if not os.path.exists(FILE_NAME):
        return {}

    try:
        with open(FILE_NAME, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}


def save_data(data):
    try:
        with open(FILE_NAME, "w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )
    except Exception as e:
        print("Xotirani saqlashda xato:", e)


user_data = load_data()


# =========================================================
# USERNI BOSHLASH
# =========================================================

def init_user(chat_id):

    chat_id = str(chat_id)

    if chat_id not in user_data:

        user_data[chat_id] = {
            "links": [],
            "current_num": 1,

            # Standart bezaklar
            "separator": "➿➿➿➿➿➿",
            "prefix": "👉",
            "suffix": "👈"
        }

        save_data(user_data)


# =========================================================
# TELEGRAM UTF-16 OFFSETNI PYTHON INDEXGA O'TKAZISH
# =========================================================

def utf16_to_python_index(text, utf16_index):

    encoded = text.encode("utf-16-le")

    byte_index = utf16_index * 2

    if byte_index > len(encoded):
        byte_index = len(encoded)

    try:
        return len(
            encoded[:byte_index].decode(
                "utf-16-le",
                errors="ignore"
            )
        )
    except Exception:
        return len(text)


# =========================================================
# PREMIUM / CUSTOM EMOJI
# =========================================================

def parse_premium_emojis(message):

    text = message.text or ""

    entities = message.entities or []

    custom_entities = []

    for entity in entities:

        if entity.type == "custom_emoji":

            custom_entities.append(entity)

    if not custom_entities:
        return text

    replacements = []

    for entity in custom_entities:

        start = utf16_to_python_index(
            text,
            entity.offset
        )

        end = utf16_to_python_index(
            text,
            entity.offset + entity.length
        )

        fallback = text[start:end]

        emoji_id = entity.custom_emoji_id

        # HTML maxsus belgilarini himoyalash
        fallback = html.escape(fallback)

        html_tag = (
            f'<tg-emoji emoji-id="{emoji_id}">'
            f'{fallback}'
            f'</tg-emoji>'
        )

        replacements.append(
            (start, end, html_tag)
        )

    # Orqadan oldinga almashtiramiz
    replacements.sort(
        key=lambda x: x[0],
        reverse=True
    )

    for start, end, html_tag in replacements:

        text = (
            text[:start]
            + html_tag
            + text[end:]
        )

    return text


# =========================================================
# /START
# =========================================================

@bot.message_handler(commands=["start"])
def start_command(message):

    chat_id = str(message.chat.id)

    init_user(chat_id)

    bot.reply_to(
        message,
        "👋 <b>Salom!</b>\n\n"
        "🔗 Menga Telegram havolalarini yuboring.\n\n"
        "Bot avtomatik ravishda:\n"
        "• Qism raqamini beradi\n"
        "• Havolalarni saqlaydi\n"
        "• Premium emoji bezaklarini saqlaydi\n\n"
        "⚙️ Buyruqlar:\n\n"
        "🔄 /tozala — xotirani tozalash\n"
        "🔢 /raqam 1 — raqamni belgilash\n"
        "🎨 /bezak — bezaklarni o'zgartirish"
    )


# =========================================================
# /TOZALA
# =========================================================

@bot.message_handler(commands=["tozala"])
def clear_data(message):

    chat_id = str(message.chat.id)

    init_user(chat_id)

    user_data[chat_id]["links"] = []

    user_data[chat_id]["current_num"] = 1

    save_data(user_data)

    bot.reply_to(
        message,
        "✅ <b>Xotira tozalandi!</b>\n\n"
        "Endi birinchi havolani yuboring."
    )


# =========================================================
# /RAQAM
# =========================================================

@bot.message_handler(commands=["raqam"])
def set_number(message):

    chat_id = str(message.chat.id)

    init_user(chat_id)

    try:

        parts = message.text.split()

        if len(parts) < 2:
            raise ValueError

        num = int(parts[1])

        if num < 1:
            raise ValueError

        user_data[chat_id]["current_num"] = num

        save_data(user_data)

        bot.reply_to(
            message,
            f"✅ Qism raqami <b>{num}</b> dan boshlanadi."
        )

    except Exception:

        bot.reply_to(
            message,
            "⚠️ <b>Xato format!</b>\n\n"
            "To'g'ri yozilishi:\n"
            "<code>/raqam 10</code>"
        )


# =========================================================
# /BEZAK YORDAM
# =========================================================

@bot.message_handler(
    commands=["bezak"]
)
def apply_bezak(message):

    chat_id = str(message.chat.id)

    init_user(chat_id)

    # Faqat /bezak yuborilgan bo'lsa
    if message.text.strip() == "/bezak":

        bot.reply_to(
            message,
            "🎨 <b>Bezak sozlash</b>\n\n"
            "Quyidagi formatda yuboring:\n\n"
            "<code>/bezak Chiziq | Oldidagi | Keyingisi</code>\n\n"
            "Masalan:\n"
            "<code>/bezak ➿➿➿ | 🔥 | 💎</code>\n\n"
            "💎 Telegram Premium emoji ham ishlatishingiz mumkin."
        )

        return

    try:

        # Premium emoji'larni HTML formatga o'tkazamiz
        premium_text = parse_premium_emojis(message)

        # /bezak ni olib tashlash
        if premium_text.startswith("/bezak"):

            text = premium_text[
                len("/bezak"):
            ].strip()

        else:

            text = premium_text

        # | orqali ajratamiz
        parts = text.split("|")

        if len(parts) != 3:

            bot.reply_to(
                message,
                "⚠️ <b>Format xato!</b>\n\n"
                "3 ta qism bo'lishi kerak:\n\n"
                "<code>/bezak Chiziq | Oldidagi | Keyingisi</code>"
            )

            return

        separator = parts[0].strip()

        prefix = parts[1].strip()

        suffix = parts[2].strip()

        # Bo'sh bo'lmasligi kerak
        if not separator:
            bot.reply_to(
                message,
                "⚠️ Chiziq bo'sh bo'lmasin."
            )
            return

        if not prefix:
            bot.reply_to(
                message,
                "⚠️ Oldidagi bezak bo'sh bo'lmasin."
            )
            return

        if not suffix:
            bot.reply_to(
                message,
                "⚠️ Keyingi bezak bo'sh bo'lmasin."
            )
            return

        # Saqlash
        user_data[chat_id]["separator"] = separator

        user_data[chat_id]["prefix"] = prefix

        user_data[chat_id]["suffix"] = suffix

        save_data(user_data)

        bot.reply_to(
            message,
            "✅ <b>Bezaklar muvaffaqiyatli saqlandi!</b>\n\n"
            "Endi havola yuboring."
        )

    except Exception as e:

        print("BEZAK XATOSI:", e)

        bot.reply_to(
            message,
            "⚠️ Bezakni saqlashda xatolik yuz berdi.\n\n"
            "Formatni tekshiring."
        )


# =========================================================
# HAVOLALARNI QABUL QILISH
# =========================================================

@bot.message_handler(
    content_types=["text"]
)
def handle_links(message):

    chat_id = str(message.chat.id)

    init_user(chat_id)

    text = message.text.strip()

    # Buyruqlarni bu yerda qayta ushlamaslik
    if text.startswith("/"):
        return

    # Havola tekshirish
    if (
        text.startswith("http://")
        or text.startswith("https://")
        or text.startswith("t.me/")
        or text.startswith("www.")
    ):

        num = user_data[chat_id]["current_num"]

        # Havolani saqlash
        user_data[chat_id]["links"].append(
            {
                "num": num,
                "url": text
            }
        )

        # Keyingi raqam
        user_data[chat_id]["current_num"] += 1

        save_data(user_data)

        # Bezaklarni olish
        sep = user_data[chat_id]["separator"]

        pref = user_data[chat_id]["prefix"]

        suff = user_data[chat_id]["suffix"]

        # Natijani yaratish
        final_msg = ""

        for item in user_data[chat_id]["links"]:

            url = html.escape(
                item["url"],
                quote=True
            )

            final_msg += (
                f"{sep}\n"
                f"  {pref} "
                f"<a href=\"{url}\">"
                f"{item['num']} - qism"
                f"</a> "
                f"{suff}\n"
            )

        final_msg += sep

        # Telegramga yuborish
        try:

            bot.reply_to(
                message,
                final_msg,
                parse_mode="HTML",
                disable_web_page_preview=True
            )

        except Exception as e:

            print("HTML yuborishda xato:", e)

            bot.reply_to(
                message,
                "⚠️ Xabarni yuborishda xatolik yuz berdi."
            )

    else:

        bot.reply_to(
            message,
            "🔗 <b>Iltimos, Telegram havolasini yuboring.</b>\n\n"
            "Masalan:\n"
            "<code>https://t.me/kanal/123</code>"
        )


# =========================================================
# BOTNI ISHGA TUSHIRISH
# =========================================================

print("======================================")
print("🤖 Premium Emoji Link Bot ishga tushdi")
print("📱 Pydroid 3 uchun tayyor")
print("======================================")


while True:

    try:

        bot.infinity_polling(
            skip_pending=True,
            timeout=60,
            long_polling_timeout=60
        )

    except Exception as e:

        print("BOT XATOSI:", e)

        import time

        time.sleep(5)
