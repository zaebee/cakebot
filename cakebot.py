import logging

import cohere

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger('httpx').setLevel(logging.INFO)
logger = logging.getLogger(__name__)

TG_TOKEN = '6279820018:AAGiA-DaTUcozoS0vonf3kcgXc8eNgBkdUo'
COHERE_TOKEN = 'onk1aMdIZZ4P86E99JlD095UEVH7LfIUwwmEF7KQ'

llm_client = cohere.Client(COHERE_TOKEN)


async def start(update, context):
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )
    
    
async def echo(update, context):
    await update.message.reply_text(update.message.text)
  
  
async def llm(update, context):
    # TODO: call gpt/gemini api
    user_message = update.message.text
    response = llm_client.chat(message=user_message)
    
    await update.message.reply_text(f'Hey! I have got response from LLM {response.text}')
    
def main():
    """Start the bot."""
    application = Application.builder().token(TG_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('llm', llm))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    
if __name__ == '__main__':
    main()