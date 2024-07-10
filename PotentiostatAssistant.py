#!/usr/bin/env python
# pylint: disable=unused-argument
'''Load environment variables from .env file'''
# Get the bot token from the environment file
import os
from dotenv import load_dotenv

load_dotenv()
bot_token = os.getenv("BOT_TOKEN")

# Get the list of allowed users from the environment file
allowed_users = []
users = ["ALBERTO", "ALESSIO", "LLUIS", "LUIS", "PILI", "MIGUEL"]
for user in users:
    allowed_users.append(os.getenv(user))

# Convert the list of allowed users to a list of integers
allowed_users = list(map(int, allowed_users))

# Create a dictionary with the user id as the key and the user name as the value
users_dict = {int(os.getenv(user)): user for user in users}


'''Initialize OpenAI API client'''
from openai import OpenAI

# Read API key from environment
api_key = os.getenv("OPENAI_API_KEY")
# Initialize the OpenAI API client
client = OpenAI(api_key=api_key)

'''Start the bot'''

import logging

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")

# Define initial messages for the chat

messages = [
    {"role": "system", "content": "You are laboratory assistant specialized in electrochemistry, you provide accurate responses with a very snarky tone."}
]

# Define message lists for each user
for user in users:
    globals()[f"{user}_messages"] = messages.copy()

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Respond to the user's message by creating a conversation with them."""

    # Set the messages list to the user's messages list
    user_id = update.effective_user.id
    messages = globals()[f"{users_dict[user_id]}_messages"]
    
    # Get the user's message
    user_message = update.message.text

    # Add the user's message to the list of messages
    messages.append({"role": "user", "content": user_message})
    
    # Generate a response using the OpenAI API
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=0.5,
        messages=messages
    )

    # Add the system's response to the list of messages
    messages.append({"role": "system", "content": completion.choices[0].message.content})
    
    # Update the user's messages list
    globals()[f"{users_dict[user_id]}_messages"] = messages

    # Print the messages list
    print(messages,'\n')
    # Reply the user with the response
    await update.message.reply_text(completion.choices[0].message.content)
    




def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(bot_token).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start, filters=filters.User(user_id=allowed_users)))
    application.add_handler(CommandHandler("help", help_command, filters=filters.User(user_id=allowed_users)))

    # on conversation update - respond to the user's message
    application.add_handler(MessageHandler(filters=filters.User(user_id=allowed_users), callback=chat))


    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()