import os
import json
import logging
from uuid import uuid4
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import (filters, ApplicationBuilder, ContextTypes,
                          CommandHandler, MessageHandler, CallbackQueryHandler,
                          InlineQueryHandler)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import finder
import recognizer
import downloader

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

TOKEN = "6613464857:AAESmaQn5x2gUF7Non5Re0475zKbpe80Coo"


async def on_started(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id,
                                   """send a Spotify link or send the name of the song - singer""")


async def on_message_recieved(update: Update, context):

    if update.effective_chat.type != 'private':  # don't read group messages
        return
    
    message = update.message
    
    # check if it's sent using @spotifybot
    if hasattr(message.via_bot, 'full_name') and message.via_bot.full_name == "Spotify":
        message = finder.process_input(message.reply_markup.inline_keyboard[0][0]['url'])
    else:
        message = finder.process_input(message.text)
    
    if isinstance(message, tuple):
        song, singer = message
        id = finder.get_song_id(song, singer)
        meta_data = finder.find_meta_data(id)
        photo = downloader.download_cover_photo(meta_data['cover_art_url'])
        caption = f"<b>{meta_data['title']}</b> - <i>{meta_data['artist']}</i> \nreleased {meta_data['year']}\n{meta_data['album']}"
        button = [[InlineKeyboardButton("Download", callback_data=id)]]
        await context.bot.send_photo(update.effective_chat.id, photo, caption, reply_markup= InlineKeyboardMarkup(button), parse_mode='HTML')
        return

    if isinstance(message, list):
        buttons = [[InlineKeyboardButton(title, callback_data=id)] for title, id in message]
        if buttons:
            await update.message.reply_text(
                text= "search results",
                reply_to_message_id=update.message.message_id,
                reply_markup= InlineKeyboardMarkup(buttons),
                parse_mode="HTML")
            return
        await update.message.reply_text(
                text= "Nothing Found",
                reply_to_message_id=update.message.message_id)
    
    # if the recieved message is a youtube music link
    await context.bot.send_message(update.effective_chat.id, "downloading...")
    song = downloader.download_song(message)
    await context.bot.send_message(update.effective_chat.id, song)


async def on_keyboard_button_pressed(update: Update, context, optional_pram=None):

    chat_id = update.effective_chat.id
    message = update.callback_query.data
    await context.bot.send_message(chat_id, "downloading...")
    song = downloader.download_song(message)
    await context.bot.send_message(chat_id, song)


async def on_voice_recieved(update: Update, context: ContextTypes.DEFAULT_TYPE):

    audio_file = await context.bot.get_file(update.message.voice.file_id)
    await audio_file.download_to_drive(update.message.voice.file_id + '.ogg')
    await context.bot.send_message(update.effective_chat.id, 'listening...')
    try:

        with open(update.message.voice.file_id + '.ogg', mode='rb') as excerpt_data:
            song, singer = recognizer.recognize_API(excerpt_data.read())
            if song:
                id = finder.get_song_id(song, singer)
                result = downloader.download_song(id)
                await context.bot.send_message(update.effective_chat.id, result)
            else:
                await context.bot.send_message(update.effective_chat.id, 'No Match Found')
            os.remove(update.message.voice.file_id + '.ogg')
    
    except Exception as exception:
        logging.error(exception)


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query

    if query == '':
        return
    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title='some item',
            input_message_content=InputTextMessageContent('item_data'))
    ]
    await update.inline_query.answer(results)



if __name__ == '__main__':
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CallbackQueryHandler(on_keyboard_button_pressed, block=False))
    application.add_handler(CommandHandler(['start', 'help'], on_started, block=False))
    application.add_handler(MessageHandler(filters.TEXT | filters.AUDIO & (~filters.COMMAND),
                       on_message_recieved,
                       block=False))
    application.add_handler(MessageHandler(filters.VOICE, on_voice_recieved))
    application.add_handler(InlineQueryHandler(inline_query))

    application.run_polling()
