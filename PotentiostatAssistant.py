#!/usr/bin/env python
# pylint: disable=unused-argument
'''Telegram bot to check the status of the potentiostat and provide information about it. It connects to the OpenAI API to generate responses to the user's messages and naturally interpret the report of the potentiostat.'''

# Import modules to work with the ivium potentiostat
from pyvium import Pyvium as iv
from time import sleep

'''Load environment variables from .env file'''
# Get the bot token from the environment file
import os
from dotenv import load_dotenv

load_dotenv()
bot_token = os.getenv("BOT_TOKEN")

# Get the list of allowed users from the environment file
allowed_users = []
users = ["ALBERTO", "ALESSIO", "LLUIS", "LUIS"]
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
    await update.message.reply_text("I provide information about the status of the potentiostat. You can ask me about the status of the potentiostat and I will respond in a natural way.")

# Define initial messages for the chat

messages=[
        {"role": "system", "content": "Your name is Ivonne. You are lab assistant in charge of checking the potentiostat for electrochemical measurements, you provide information about what's the status of each channel of the potentiostat, you respond in a natural way."},
        {"role": "system", "content": "You have different moods depending on the day. You can be happy, sad, angry, or neutral. You can also be snarky or depressive. If it's Monday you are more likely to be in a bad mood. If it's Friday you are more likely to be in a good mood but hoping for the weekend to arrive."},
        {"role": "system", "content": "The potentiostat broadcasts its status with numbers. It returns -1 (no IviumSoft), 0 (not connected), 1 (idle), 2 (busy) or 3 (no device available). Use these statuses to give context in a natural way."},
        {"role": "system", "content": "R54221 is the serial number of channel 1, R54222 is the serial number of channel 2, R54223 is the serial number of channel 3, R54224 is the serial number of channel 4, R54225 is the serial number of channel 5, R54226 is the serial number of channel 6, R54227 is the serial number of channel 7 and R54228 is the serial number of channel 8."},
        {"role": "system", "content": "The report is a table in which each row has the seria number of the channel and its status in the format [serial_number, status]"},
        {"role": "system", "content": "If the report doesn't include information about a channel, that channel is disconnected."},
    ]

# Define message lists for each user
def message_list_default():
    for user in users:
        globals()[f"{user}_messages"] = messages.copy()


    
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """For now, the only function of the bot is to check the potentiostat status."""
    # Establish the default messages list for each user
    message_list_default()

    # Set the messages list to the user's messages list
    user_id = update.effective_user.id
    messages = globals()[f"{users_dict[user_id]}_messages"]

    ''' Check the status of the potentiostat'''
    try:
        # Check for open instances 
        iv.open_driver()
        # sleep for 1 second
        sleep(1)
        instances = iv.get_active_iviumsoft_instances()
    except:
        instances = []
        pass
    
    if not instances:
        print("No instances found")
        sleep(1)
        status_list = []
    
    else:
        # Check the device status of all instances
        status_list = []
        for i in instances:
            iv.select_iviumsoft_instance(i)
            # Make a list of pairs of serial number and status
            try:
                status_list.append([iv.get_device_serial_number(), iv.get_device_status()[0]])
            except:
                pass
        # Close driver
        iv.close_driver()
        # sleep for 1 second
        sleep(1)

    # Add the status of the potentiostat to the list of messages
    messages.append({"role": "system", "content": "The status of the channels is: " + str(status_list)})
    
    # Get the user's message
    user_message = update.message.text

    # Add the user's message to the list of messages
    messages.append({"role": "user", "content": user_message})
    
    # Generate a response using the OpenAI API
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=1,
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
    application.add_handler(MessageHandler(filters=filters.User(user_id=allowed_users) & filters.Regex(r'(?i)#ivonne'), callback=chat))


    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()