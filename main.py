import os
import logging
import psycopg2
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ConversationHandler
)

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Token (set in .env file)
TOKEN = os.getenv("BOT_TOKEN")

# Local PostgreSQL Database Credentials
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")  # Default to localhost
DB_PORT = os.getenv("DB_PORT", "5432")  # Default PostgreSQL port

# Configure logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Define states for ConversationHandler
NAME, AGE, DOB, CONTACT = range(4)

# Function to connect to the PostgreSQL database
def connect_db():
    return psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )

# Create a table for user data
def create_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            dob TEXT NOT NULL,
            contact TEXT NOT NULL
        )
        """
    )
    conn.commit()
    cursor.close()
    conn.close()

# Start command handler
async def start(update: Update, context):
    await update.message.reply_text("Hello! What is your name?")
    return NAME

# Handle user's name
async def get_name(update: Update, context):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Great! How old are you?")
    return AGE

# Handle user's age
async def get_age(update: Update, context):
    context.user_data["age"] = update.message.text
    await update.message.reply_text("Nice! What is your date of birth? (DD-MM-YYYY)")
    return DOB

# Handle user's date of birth
async def get_dob(update: Update, context):
    context.user_data["dob"] = update.message.text
    await update.message.reply_text("Finally, please provide your contact number.")
    return CONTACT

# Handle user's contact number and save data to the database
async def get_contact(update: Update, context):
    contact = update.message.text
    name = context.user_data["name"]
    age = context.user_data["age"]
    dob = context.user_data["dob"]

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (name, age, dob, contact) VALUES (%s, %s, %s, %s)",
        (name, age, dob, contact),
    )
    conn.commit()
    cursor.close()
    conn.close()

    await update.message.reply_text("Thank you! Your details have been saved.")
    return ConversationHandler.END

# Help command handler
async def help_command(update: Update, context):
    await update.message.reply_text("/start - Register yourself\n/help - Show commands\n/About - Learn about this bot")

# About command handler
async def about_command(update: Update, context):
    about_text = "This bot collects user details and stores them securely in a local PostgreSQL database."
    await update.message.reply_text(about_text)

# Cancel command handler
async def cancel(update: Update, context):
    await update.message.reply_text("Registration process canceled.")
    return ConversationHandler.END

# Main function
def main():
    create_table()  # Ensure database table exists before starting bot

    app = Application.builder().token(TOKEN).build()

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

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))

    logging.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
