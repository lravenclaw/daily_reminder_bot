import logging
from uuid import uuid4

import os
import datetime

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, InlineQueryHandler

import pytz

from settings import ACCESS_TOKEN
from settings import ADMIN_ID

import messages

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=messages.start)
    await subscribe(update, context)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=messages.commands_description)


def subscribed(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    return len(jobs) > 0


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if subscribed(update.effective_chat.id, context):
        return
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text=messages.subscribed_successfully)

    job_name = str(update.effective_chat.id)
    tz = pytz.timezone('Europe/Minsk')
    morning_time = datetime.time(hour=5, minute=0, second=0, tzinfo=tz)
    context.job_queue.run_daily(send_motivation, morning_time, chat_id=update.effective_chat.id, name=job_name)


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)

    if not current_jobs:
        return False

    for job in current_jobs:
        job.schedule_removal()

    return True


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    remove_job_if_exists(str(chat_id), context)

    await context.bot.send_message(chat_id=chat_id, text=messages.reset_successfully)


async def send_motivation(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    answer = messages.get_daily_motivation_message()
    await context.bot.send_message(chat_id=job.chat_id, text=answer, parse_mode=ParseMode.HTML)


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (update.message.from_user.id != int(ADMIN_ID)):
        await context.bot.send_message(chat_id=update.effective_chat.id, text=messages.not_admin)
        return
    
    text = f"""
    📊 Bot Statistics

    Total users: {len(context.job_queue.jobs())}
    """
        
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=messages.unknown_command)


def main() -> None:
    application = ApplicationBuilder().token(ACCESS_TOKEN).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    help_handler = CommandHandler('help', help)
    application.add_handler(help_handler)

    subscribe_handler = CommandHandler('subscribe', subscribe)
    application.add_handler(subscribe_handler)

    reset_handler = CommandHandler('reset', reset)
    application.add_handler(reset_handler)

    stats_handler = CommandHandler('stats', stats)
    application.add_handler(stats_handler)

    # Unknown command
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)

    # Unknown message
    text_message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, unknown)
    application.add_handler(text_message_handler)

    application.run_polling()

# Vercel serverless function handler
app = main

if __name__ == '__main__':
    main()
