import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize OpenAI client for OpenRouter
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Store conversation history per user
conversation_history = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Reset conversation history when user starts
    conversation_history[user_id] = []
    logging.info(f"Start command received from user {user_id}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me! I can remember our conversation.")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    logging.info(f"Received message from user {user_id}: {user_message}")
    
    # Initialize conversation history for new users
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    
    # Add user message to conversation history
    conversation_history[user_id].append({
        "role": "user",
        "content": user_message
    })
    
    # Keep only last 20 messages to avoid token limits (10 exchanges)
    if len(conversation_history[user_id]) > 20:
        conversation_history[user_id] = conversation_history[user_id][-20:]
    
    try:
        # Call OpenRouter API with conversation history
        logging.info("Sending request to OpenRouter...")
        completion = await client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://telegram.org", # Optional, for including your app on openrouter.ai rankings.
                "X-Title": "Telegram Bot", # Optional. Shows in rankings on openrouter.ai.
            },
            model="openai/gpt-3.5-turbo", # You can change this to other models supported by OpenRouter
            messages=conversation_history[user_id]
        )
        
        bot_response = completion.choices[0].message.content
        
        # Add bot response to conversation history
        conversation_history[user_id].append({
            "role": "assistant",
            "content": bot_response
        })
        
        logging.info(f"Received response from OpenRouter: {bot_response}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=bot_response)
        
    except Exception as e:
        logging.error(f"Error calling OpenRouter: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error: {str(e)}")

if __name__ == '__main__':
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN not found in .env file")
        exit(1)
        
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    chat_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), chat)
    
    application.add_handler(start_handler)
    application.add_handler(chat_handler)
    
    print("Bot is running...")
    application.run_polling()
