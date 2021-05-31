import logging
from urllib.parse import quote

from pyrogram import Client, emoji, filters
from pyrogram.errors import UserNotParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultCachedDocument

from utils import get_search_results
from info import MAX_RESULTS, CACHE_TIME, SHARE_BUTTON_TEXT, AUTH_USERS, AUTH_CHANNEL

logger = logging.getLogger(__name__)
cache_time = 0 if AUTH_USERS or AUTH_CHANNEL else CACHE_TIME


@Client.on_inline_query(filters.user(AUTH_USERS) if AUTH_USERS else None)
async def answer(bot, query):
    """Show search results for given inline query"""

    if AUTH_CHANNEL and not await is_subscribed(bot, query):
        await query.answer(results=[],
                           cache_time=0,
                           switch_pm_text='ඔබට නාලිකාව දායක විය යුතුය',
                           switch_pm_parameter="subscribe")
        return

    results = []
    if '|' in query.query:
        string, file_type = query.query.split('|', maxsplit=1)
        string = string.strip()
        file_type = file_type.strip().lower()
    else:
        string = query.query.strip()
        file_type = None

    offset = int(query.offset or 0)
    reply_markup = get_reply_markup(bot.username, query=string)
    files, next_offset = await get_search_results(string,
                                                  file_type=file_type,
                                                  max_results=MAX_RESULTS,
                                                  offset=offset)

    for file in files:
        results.append(
            InlineQueryResultCachedDocument(
                title=file.file_name,
                file_id=file.file_id,
                caption=file.caption or "📢: @brainstromch",
                description=f'Size: {get_size(file.file_size)}\nType: {file.file_type}',
                reply_markup=reply_markup))

    if results:
        switch_pm_text = f"{emoji.FILE_FOLDER} ප්රතිපල"
        if string:
            switch_pm_text += f" for {string}"

        await query.answer(results=results,
                           cache_time=cache_time,
                           switch_pm_text=switch_pm_text,
                           switch_pm_parameter="start",
                           next_offset=str(next_offset))
    else:

        switch_pm_text = f'{emoji.CROSS_MARK} ප්‍රතිඵල නොමැත'
        if string:
            switch_pm_text += f' for "{string}"'

        await query.answer(results=[],
                           cache_time=cache_time,
                           switch_pm_text=switch_pm_text,
                           switch_pm_parameter="හරි")


def get_reply_markup(username, query):
    url = 't.me/share/url?url=' + quote(SHARE_BUTTON_TEXT.format(username=username))
    buttons = [[
        InlineKeyboardButton('නැවත සොයන්න', switch_inline_query_current_chat=query),
        InlineKeyboardButton('බෙදාහරින්න බොට්ව', url=url),
        InlineKeyboardButton('පොත ඉල්ලන්න', url="https://t.me/BSSlk_bot"),
    ]]
    return InlineKeyboardMarkup(buttons)


def get_size(size):
    """Get size in readable format"""

    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])


async def is_subscribed(bot, query):
    try:
        user = await bot.get_chat_member(AUTH_CHANNEL, query.from_user.id)
    except UserNotParticipant:
        pass
    except Exception as e:
        logger.exception(e)
    else:
        if not user.status == 'kicked':
            return True

    return False
