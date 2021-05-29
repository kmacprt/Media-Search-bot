import os
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from info import START_MSG, CHANNELS, ADMINS, INVITE_MSG
from utils import Media

logger = logging.getLogger(__name__)


@Client.on_message(filters.command('start'))
async def start(bot, message):
    """Start command handler"""
    if len(message.command) > 1 and message.command[1] == 'subscribe':
        await message.reply(INVITE_MSG)
    else:
        buttons = [[
            InlineKeyboardButton('සොයන්න.🔎', switch_inline_query_current_chat=''),
            InlineKeyboardButton('Inline වෙත යන්න', switch_inline_query=''),
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply(START_MSG, reply_markup=reply_markup)


@Client.on_message(filters.command('channel') & filters.user(ADMINS))
async def channel_info(bot, message):
    """Send basic information of channel"""
    if isinstance(CHANNELS, (int, str)):
        channels = [CHANNELS]
    elif isinstance(CHANNELS, list):
        channels = CHANNELS
    else:
        raise ValueError("බලාපොරොත්තු නොවූ ආකාරයේ චැනල් වර්ග")

    text = '📑 **සුචිගත කළ නාලිකා/සමුහ**\n'
    for channel in channels:
        chat = await bot.get_chat(channel)
        if chat.username:
            text += '\n@' + chat.username
        else:
            text += '\n' + chat.title or chat.first_name

    text += f'\n\n**මුළු:** {len(CHANNELS)}'

    if len(text) < 4096:
        await message.reply(text)
    else:
        file = 'සුචිගත කළ නාලිකා.txt'
        with open(file, 'w') as f:
            f.write(text)
        await message.reply_document(file)
        os.remove(file)


@Client.on_message(filters.command('total') & filters.user(ADMINS))
async def total(bot, message):
    """Show total files in database"""
    msg = await message.reply("සකසමින්...⏳", quote=True)
    try:
        total = await Media.count_documents()
        await msg.edit(f'📁 ගොනු සුරකින ලදි: {total}')
    except Exception as e:
        logger.exception('සම්පූර්ණ ලිපිගොනු පරීක්ෂා කිරීමට අපොහොසත් විය')
        await msg.edit(f'Error: {e}')


@Client.on_message(filters.command('logger') & filters.user(ADMINS))
async def log_file(bot, message):
    """Send log file"""
    try:
        await message.reply_document('TelegramBot.log')
    except Exception as e:
        await message.reply(str(e))


@Client.on_message(filters.command('delete') & filters.user(ADMINS))
async def delete(bot, message):
    """Delete file from database"""
    reply = message.reply_to_message
    if reply and reply.media:
        msg = await message.reply("සකසමින්⏳", quote=True)
    else:
        await message.reply('ඔබට මැකීමට අවශ්‍ය ලිපිගොනු වලට පිළිතුරු දෙන්න /delete විදානය භාවිත කරන්න.', quote=True)
        return

    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media is not None:
            break
    else:
        await msg.edit('මෙය සහාය දක්වන ගොනු ආකෘතියක් නොවේ')
        return

    result = await Media.collection.delete_one({
        'file_name': media.file_name,
        'file_size': media.file_size,
        'mime_type': media.mime_type,
        'caption': reply.caption
    })
    if result.deleted_count:
        await msg.edit('දත්ත සමුදායෙන් ගොනුව සාර්ථකව මකා දමනු ලැබේ')
    else:
        await msg.edit('ගොනුව දත්ත ගබඩාවේ නොමැත')
