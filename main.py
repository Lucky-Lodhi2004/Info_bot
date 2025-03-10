import os
import logging
import psycopg2
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext

# Load environment variables
load_dotenv()

# Telegram Bot Token from Railway Environment Variables
TOKEN = os.getenv("BOT_TOKEN")
DB_URL = os.getenv("DATABASE_URL")

# Database connection setup
conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# States for ConversationHandler
NAME, AGE, DOB, CONTACT = range(4)

# Create the users table if it doesn't exist
cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        user_id BIGINT UNIQUE,
        name TEXT,
        age INT,
        dob TEXT,
        contact TEXT
    )
""")
conn.commit()


async def start(update: Update, context: CallbackContext) -> int:
    """Starts the conversation by asking for the user's name."""
    await update.message.reply_text("Hello! What's your name?")
    return NAME


async def get_name(update: Update, context: CallbackContext) -> int:
    """Stores the name and asks for the age."""
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Great! Now, how old are you?")
    return AGE


async def get_age(update: Update, context: CallbackContext) -> int:
    """Stores the age and asks for the date of birth."""
    context.user_data["age"] = update.message.text
    await update.message.reply_text("Thanks! Please enter your date of birth (YYYY-MM-DD).")
    return DOB


async def get_dob(update: Update, context: CallbackContext) -> int:
    """Stores the date of birth and asks for the contact number."""
    context.user_data["dob"] = update.message.text
    await update.message.reply_text("Almost done! Please enter your contact number.")
    return CONTACT


async def get_contact(update: Update, context: CallbackContext) -> int:
    """Stores the contact number and saves user data to PostgreSQL."""
    user_id = update.message.from_user.id
    name = context.user_data["name"]
    age = context.user_data["age"]
    dob = context.user_data["dob"]
    contact = update.message.text

    try:
        cur.execute("INSERT INTO users (user_id, name, age, dob, contact) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, name, age, dob, contact))
        conn.commit()
        await update.message.reply_text("Your details have been saved successfully!")
    except Exception as e:
        logger.error(f"Database error: {e}")
        await update.message.reply_text("An error occurred while saving your data.")

    return ConversationHandler.END


async def help_command(update: Update, context: CallbackContext) -> None:
    """Provides help information."""
    help_text = (
        "/start - Register yourself with the bot.\n"
        "/help - Show this help message.\n"
        "/about - Learn about this bot."
    )
    await update.message.reply_text(help_text)


async def about_command(update: Update, context: CallbackContext) -> None:
    """Provides information about the bot."""
    about_text = (
        "This bot collects and stores user details securely.\n"
        "Features:\n"
        "- Collects user details interactively.\n"
        "- Stores details in a secure PostgreSQL database.\n"
        "- Provides information about commands.\n"
        "All data is securely stored on Railway.app."
    )
    await update.message.reply_text(about_text)


async def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels the conversation."""
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END


def main():
    """Main function to start the bot."""
    app = Application.builder().token(TOKEN).build()

    # Define conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dob)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Command handlers
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))

    # Start polling
    app.run_polling()


if __name__ == "__main__":
    main()

