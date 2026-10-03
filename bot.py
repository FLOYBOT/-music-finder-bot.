import os
import asyncio
from urllib.parse import quote_plus

import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN")

LRCLIB_SEARCH = "https://lrclib.net/api/search"
dp = Dispatcher()

def source_buttons(title: str, artist: str):
    q = quote_plus(f"{title} {artist}")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ YouTube", url=f"https://www.youtube.com/results?search_query={q}")],
        [InlineKeyboardButton(text="🎵 Spotify", url=f"https://open.spotify.com/search/{q}")],
        [InlineKeyboardButton(text="🍎 Apple Music", url=f"https://music.apple.com/us/search?term={q}")],
    ])

async def search_lrclib(query: str):
    timeout = aiohttp.ClientTimeout(total=12)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(LRCLIB_SEARCH, params={"q": query}) as resp:
            resp.raise_for_status()
            return await resp.json()

def format_result(item):
    title = item.get("trackName") or item.get("name") or "Неизвестный трек"
    artist = item.get("artistName") or "Неизвестный исполнитель"
    album = item.get("albumName") or "—"
    duration = item.get("duration")
    if isinstance(duration, (int, float)):
        mins, secs = divmod(int(duration), 60)
        duration_text = f"{mins}:{secs:02d}"
    else:
        duration_text = "—"
    return title, artist, album, duration_text

async def do_search(message: Message, query: str):
    try:
        results = await search_lrclib(query)
    except Exception:
        await message.answer("Не удалось выполнить поиск. Попробуй ещё раз через несколько секунд.")
        return
    if not results:
        await message.answer("Ничего не нашёл. Попробуй название + исполнителя или несколько слов из текста.")
        return
    for item in results[:5]:
        title, artist, album, duration = format_result(item)
        text = f"🎵 <b>{title}</b>\n👤 {artist}\n💿 {album}\n⏱ {duration}"
        await message.answer(text, parse_mode="HTML", reply_markup=source_buttons(title, artist))

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "🎧 <b>Music Finder</b>\n\n"
        "Напиши название песни, исполнителя или несколько слов из текста — я попробую найти трек.\n\n"
        "Пример: <code>Blinding Lights The Weeknd</code>",
        parse_mode="HTML",
    )

@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer("Отправь название песни, имя исполнителя или фрагмент текста.")

@dp.message(F.text)
async def text_search(message: Message):
    query = message.text.strip()
    if len(query) < 2:
        await message.answer("Напиши хотя бы несколько символов для поиска.")
        return
    await do_search(message, query)

async def main():
    bot = Bot(TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
