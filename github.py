import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart

# ---------------- CONFIG ----------------
BOT_TOKEN = "123qwe"
API_KEY = "sk-1100"
# ----------------------------------------

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ---------------- USER DATA ----------------
users = {}

# Language texts
texts = {
    "uz": {
        "start": "👋 Salom! Tilni tanlang:",
        "ready": "✅ Tayyor! Savolingizni yozing:",
        "limit": "❌ Limit tugadi!",
        "error": "⚠️ Xatolik yuz berdi!"
    },
    "en": {
        "start": "👋 Hello! Choose your language:",
        "ready": "✅ Ready! Ask me anything:",
        "limit": "❌ Limit reached!",
        "error": "⚠️ Something went wrong!"
    },
    "ru": {
        "start": "👋 Привет! Выберите язык:",
        "ready": "✅ Готово! Задайте вопрос:",
        "limit": "❌ Лимит достигнут!",
        "error": "⚠️ Произошла ошибка!"
    }
}

# Language selection keyboard
lang_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🇺🇿 Uzbek")],
        [KeyboardButton(text="🇬🇧 English")],
        [KeyboardButton(text="🇷🇺 Russian")]
    ],
    resize_keyboard=True
)

# ---------------- AI FUNCTION ----------------
async def ask_ai(text, lang):
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = f"Reply in {lang}. Be helpful, friendly, and concise."

    data = {
        "model": "openai/gpt-4",   # <-- valid model
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        "max_tokens": 50  # safe for free plan
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                result = await response.json()
                print("API RESPONSE:", result)
                if "choices" in result and result["choices"]:
                    return result["choices"][0]["message"]["content"]
                elif "error" in result:
                    return f"⚠️ API ERROR: {result['error']['message']}"
                return None
    except Exception as e:
        print("API ERROR:", e)
        return None

# ---------------- START COMMAND ----------------
@dp.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    
    # If user exists, don't reset count, just let them choose language again
    if user_id not in users:
        users[user_id] = {"lang": None, "count": 0}
    
    await message.answer(texts["en"]["start"], reply_markup=lang_kb)
# ---------------- LANGUAGE SELECTION ----------------
@dp.message(F.text.in_(["🇺🇿 Uzbek", "🇬🇧 English", "🇷🇺 Russian"]))
async def set_language(message: Message):
    user_id = message.from_user.id
    
    if "Uzbek" in message.text:
        lang = "uz"
    elif "English" in message.text:
        lang = "en"
    else:
        lang = "ru"
    
    users[user_id]["lang"] = lang
    users[user_id]["count"] = 0
    await message.answer(texts[lang]["ready"])

# ---------------- CHAT HANDLER ----------------
@dp.message()
async def chat(message: Message):
    user_id = message.from_user.id
    
    # Language not chosen yet
    if user_id not in users or users[user_id]["lang"] is None:
        await message.answer("⚠️ Please choose language first", reply_markup=lang_kb)
        return

    lang = users[user_id]["lang"]

    # Limit check
    if users[user_id]["count"] >= 5:
        await message.answer(texts[lang]["limit"])
        return

    users[user_id]["count"] += 1

    reply = await ask_ai(message.text, lang)
    if reply:
        await message.answer(reply)
    else:
        await message.answer(texts[lang]["error"])

# ---------------- RUN BOT ----------------
async def main():
    print("✅ Bot is running... Waiting for messages 👀")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
