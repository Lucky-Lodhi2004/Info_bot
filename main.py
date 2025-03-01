import logging
import mysql.connector
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
from mysql.connector import Error
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Setup logging for debugging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# MySQL connection setup (using environment variables)
DATABASE_HOST = "mysql-1c88708d-peeyushh.l.aivencloud.com"
DATABASE_USER = "avnadmin"
DATABASE_PASSWORD = "AVNS_iDydXCW0_gyIYRZkAGb"
DATABASE_NAME = "bot" 

# Define conversation states
NAME, AGE, DOB, CONTACT = range(4)

# Global variables to store user data
name = None
age = None
dob = None
contact = None

async def start(update: Update, context: CallbackContext) -> int:
    """Start the conversation and ask for the user's name."""
    user = update.message.from_user
    global name
    name = None  # Reset user data
    global age
    age = None
    global dob
    dob = None
    global contact
    contact = None
    
    await update.message.reply_text(f"Hello {user.first_name}! Let's start by gathering your details.")
    await update.message.reply_text("What is your name?")
    return NAME

async def handle_name(update: Update, context: CallbackContext) -> int:
    """Handle user's name input."""
    global name
    name = update.message.text
    await update.message.reply_text("How old are you?")
    return AGE

async def handle_age(update: Update, context: CallbackContext) -> int:
    """Handle user's age input."""
    global age
    age = update.message.text
    await update.message.reply_text("What is your date of birth?")
    return DOB

async def handle_dob(update: Update, context: CallbackContext) -> int:
    """Handle user's date of birth input."""
    global dob
    dob = update.message.text
    await update.message.reply_text("Please provide your contact number.")
    return CONTACT


async def save_to_database(user) -> None:
    """Save user data to the MySQL database on Railway"""
    try:
        connection = mysql.connector.connect(
            host=DATABASE_HOST,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            database=DATABASE_NAME,
            auth_plugin = "mysql_native_password"
        )
        cursor = connection.cursor()
        
        query = """
        INSERT INTO users (name, age, dob, contact)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (name, age, dob, contact))
        connection.commit()
        
    except Error as e:
        logger.error(f"Error saving to database: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

async def handle_contact(update: Update, context: CallbackContext) -> int:
    """Handle user's contact number input and save the data."""
    global contact
    contact = update.message.text
    await save_to_database(update.message.from_user)
    await update.message.reply_text("Thank you! Your data has been saved.")
    return ConversationHandler.END
  
async def help_command(update: Update, context: CallbackContext) -> None:
    """Help command showing available bot commands."""
    await update.message.reply_text("/start - Begin data collection\n/help - Show this help message\n/About - Information about the bot.")

async def about_command(update: Update, context: CallbackContext) -> None:
    """About command showing the features and working of the bot."""
    about_text = (
        "This bot collects user information including:\n"
        "- Name\n"
        "- Age\n"
        "- Date of Birth\n"
        "- Contact Number\n\n"
        "Once collected, this data is stored in a MySQL database hosted on Railway.app.\n"
        "The bot provides three commands:\n"
        "/start - Collects user data\n"
        "/help - Shows the bot commands\n"
        "/About - Displays information about the bot"
    )
    await update.message.reply_text(about_text)

def main() -> None:
    """Main function to start the bot."""
    # Telegram bot token from BotFather
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Define the conversation handler with the states
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_age)],
            DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_dob)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_contact)],
        },
        fallbacks=[],
    )

    # Command handlers
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("About", about_command))

    # Add the conversation handler to the application
    application.add_handler(conversation_handler)

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
