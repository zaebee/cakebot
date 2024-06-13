import os
import logging

import cohere

from dotenv import load_dotenv
from telegram import ForceReply, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters)

from orders import actual_orders

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger('httpx').setLevel(logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

COHERE_TOKEN = os.getenv('COHERE_TOKEN')
TG_TOKEN = os.getenv('TG_TOKEN')

BISCUIT, TOPPINGS, PHOTO, EXTRA = range(4)

llm_client = cohere.Client(COHERE_TOKEN)


class Bot:
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Starts the conversation and asks the user about biscuit."""
        reply_keyboard = [['Ванильный', 'Радуга', 'Шоколадный']]

        await update.message.reply_text(
            'Привет! Я конструктор тортов. Помогу вам собрать свой тортик.'
            'Отправь /cancel чтобы остановить диалог.\n\n'
            'Какой вам нужен бисквит?',
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, 
                one_time_keyboard=True, 
                input_field_placeholder='Выберите бисквит'
            ),
        )
        return BISCUIT

    async def biscuit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        return TOPPINGS

    async def toppings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Stores the selected biscuit and asks for toppings."""
        user = update.message.from_user
        logger.info("Toppings of %s: %s", user.first_name, update.message.text)
        await update.message.reply_text(
            "I see! Please send me a photo of yourself, "
            "so I know what you look like, or send /skip if you don't want to.",
            reply_markup=ReplyKeyboardRemove(),
        )

        return PHOTO

    async def photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Stores the toppings and asks for a decor examples."""
        user = update.message.from_user
        photo_file = await update.message.photo[-1].get_file()
        await photo_file.download_to_drive("cake_photo.jpg")
        logger.info("Cake Decor of %s: %s", user.first_name, "cake_photo.jpg")
        await update.message.reply_text(
            "Gorgeous! Now, send me your location please, or send /skip if you don't want to."
        )

        return EXTRA

    async def skip_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Skips the photo and asks for a location."""
        user = update.message.from_user
        logger.info("User %s did not send a photo.", user.first_name)
        await update.message.reply_text(
            "I bet you look great! Now, send me your location please, or send /skip."
        )

        return EXTRA


    async def extra(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Stores the info about the user and ends the conversation."""
        user = update.message.from_user
        logger.info("Extra of %s: %s", user.first_name, update.message.text)
        await update.message.reply_text("Thank you! I hope we can talk again some day.")

        return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancels and ends the conversation."""
        user = update.message.from_user
        logger.info("User %s canceled the conversation.", user.first_name)
        await update.message.reply_text(
            "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
        )

        return ConversationHandler.END

    async def orders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gets orders from external gsheet file."""
        user = update.effective_user
        orders = actual_orders()
        message = rf"""
            Hi {user.mention_markdown_v2()}\!
            List of cake orders:
            ```{orders.to_markdown(index=False)}```
        """
        await update.message.reply_text(
            message, parse_mode='MarkdownV2',
            # reply_markup=ForceReply(selective=True),
        )

    async def llm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # TODO: call gpt/gemini api
        user_message = update.message.text
        response = llm_client.chat(message=user_message)

        await update.message.reply_text(f'Hey! I have got response from LLM {response.text}')


def main():
    """Start the bot."""
    bot = Bot()
    application = Application.builder().token(TG_TOKEN).build()
    application.add_handler(CommandHandler('orders', bot.orders))
    application.add_handler(CommandHandler('llm', bot.llm))
    # application.add_handler(MessageHandler(
    #     filters.TEXT & ~filters.COMMAND, bot.echo))

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', bot.start)],
        states={
            BISCUIT: [MessageHandler(filters.Regex('^(Ванильный|Радуга|Шоколадный)$'), bot.toppings)],
            PHOTO: [MessageHandler(filters.PHOTO, bot.photo), CommandHandler('skip', bot.skip_photo)],
            EXTRA: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.extra)],
        },
        fallbacks=[CommandHandler('cancel', bot.cancel)],
    )

    application.add_handler(conv_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
