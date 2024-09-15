import logging
from uuid import uuid4

import os
import datetime

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

import pytz

import asyncio
import html
from dataclasses import dataclass
from http import HTTPStatus
import uvicorn
from asgiref.wsgi import WsgiToAsgi
from flask import Flask, Response, abort, make_response, request

from telegram import Update
from telegram.constants import ParseMode

from telegram.ext import (
    Application,
    CallbackContext,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ExtBot,
    TypeHandler,
    MessageHandler,
    filters,
)

from settings import ACCESS_TOKEN, ADMIN_ID, PORT, URL
import messages

logging.basicConfig(

    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO

)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

flask_app = Flask(__name__)

@dataclass
class WebhookUpdate:
    """Simple dataclass to wrap a custom update type"""
    user_id: int
    payload: str


class CustomContext(CallbackContext[ExtBot, dict, dict, dict]):
    """
    Custom CallbackContext class that makes `user_data` available for updates of type
    `WebhookUpdate`.
    """
    @classmethod
    def from_update(
        cls,
        update: object,
        application: "Application",
    ) -> "CustomContext":
        if isinstance(update, WebhookUpdate):
            return cls(application=application, user_id=update.user_id)
        return super().from_update(update, application)


async def webhook_update(update: WebhookUpdate, context: CustomContext) -> None:
    """Handle custom updates."""
    chat_member = await context.bot.get_chat_member(chat_id=update.user_id, user_id=update.user_id)
    payloads = context.user_data.setdefault("payloads", [])
    payloads.append(update.payload)
    combined_payloads = "</code>\n• <code>".join(payloads)
    text = (
        f"The user {chat_member.user.mention_html()} has sent a new payload. "
        f"So far they have sent the following payloads: \n\n• <code>{combined_payloads}</code>"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text, parse_mode=ParseMode.HTML)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display a message with instructions on how to use this bot."""
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


async def webhook_set():
    """Check if the webhook is set up."""
    response = requests.get(f"https://api.telegram.org/bot{ACCESS_TOKEN}/getWebhookInfo").json()
    if response["result"]["url"] == f"{URL}/telegram":
        return true
    return false

async def main() -> None:
    """Set up PTB application and a web application for handling the incoming requests."""
    context_types = ContextTypes(context=CustomContext)

    # Here we set updater to None because we want our custom webhook server to handle the updates
    # and hence we don't need an Updater instance
    application = (
        Application.builder().token(ACCESS_TOKEN).updater(None).context_types(context_types).build()
    )

    # register handlers
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

    # Register the webhook handler
    application.add_handler(TypeHandler(type=WebhookUpdate, callback=webhook_update))

    # Pass webhook settings to telegram
    #await application.bot.set_webhook(url=f"{URL}/telegram", allowed_updates=Update.ALL_TYPES)

    @flask_app.post("/telegram")  # type: ignore[misc]
    async def telegram() -> Response:
        """Handle incoming Telegram updates by putting them into the `update_queue`"""
        await application.update_queue.put(Update.de_json(data=request.json, bot=application.bot))
        return Response(status=HTTPStatus.OK)

    @flask_app.route("/submitpayload", methods=["GET", "POST"])  # type: ignore[misc]
    async def custom_updates() -> Response:
        """
        Handle incoming webhook updates by also putting them into the `update_queue` if
        the required parameters were passed correctly.
        """
        try:
            user_id = int(request.args["user_id"])
            payload = request.args["payload"]
        
        except KeyError:
            abort(
                HTTPStatus.BAD_REQUEST,
                "Please pass both `user_id` and `payload` as query parameters.",
            )
        
        except ValueError:
            abort(HTTPStatus.BAD_REQUEST, "The `user_id` must be a string!")


        await application.update_queue.put(WebhookUpdate(user_id=user_id, payload=payload))
        return Response(status=HTTPStatus.OK)

    @flask_app.get("/healthcheck")  # type: ignore[misc]
    async def health() -> Response:
        """For the health endpoint, reply with a simple plain text message."""
        response = make_response("The bot is still running fine :)", HTTPStatus.OK)
        response.mimetype = "text/plain"
        return response

    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=WsgiToAsgi(flask_app),
            port=PORT,
            use_colors=False,
            host="0.0.0.0",
        )
    )

    # Run application and webserver together
    async with application:
        await application.start()
        await webserver.serve()
        #if not await webhook_set():
        #    await application.bot.set_webhook(url=f"{URL}/telegram", allowed_updates=Update.ALL_TYPES)
        await application.stop()


if __name__ == "__main__":
    asyncio.run(main())

