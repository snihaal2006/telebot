"""
Telegram Attendance Bot
Allows users to mark students as absent by entering row numbers (comma-separated)
Supports session management: Add Absent or New Absent
"""

import logging
import pandas as pd
import shutil
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import config
from fastapi import FastAPI, Request, Response
from contextlib import asynccontextmanager
import uvicorn

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    welcome_message = (
        "👋 Welcome to the Attendance Bot!\n\n"
        "I can help you mark students as absent in the attendance sheet.\n\n"
        "📝 How to use:\n"
        "1. I'll ask if you want to 'Add Absent' or start 'New Absent'\n"
        "2. Send registration number endings (single or comma-separated)\n"
        "   Example: '1' (matches reg ending in 01)\n"
        "   Example: '1,3,5,7' or '11,22,33'\n"
        "3. Get the updated Excel file\n\n"
        "Use /help for more information."
    )
    
    # Show session selection keyboard
    keyboard = [
        [
            InlineKeyboardButton("➕ Add Absent", callback_data='add_absent'),
            InlineKeyboardButton("🆕 New Absent", callback_data='new_absent')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message)
    await update.message.reply_text(
        "Choose your session mode:",
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "📚 *Attendance Bot Help*\n\n"
        "*Commands:*\n"
        "/start - Start the bot and choose session mode\n"
        "/help - Show this help message\n\n"
        "*Session Modes:*\n"
        "• *Add Absent* - Continue editing existing working file\n"
        "• *New Absent* - Start fresh from original (all PRESENT)\n\n"
        "*How to mark absent:*\n"
        "1. Choose session mode (Add/New)\n"
        "2. Send registration number endings:\n"
        "   - Single digit: '1' → matches reg ending in 01\n"
        "   - Double digit: '11' → matches reg ending in 11\n"
        "   - Multiple: '1,3,5,7' or '11,22,33'\n"
        "3. Receive updated Excel file\n\n"
        "*Notes:*\n"
        "- Original file is never modified\n"
        "- Single digits are auto-padded (1 → 01)\n"
        "- Spaces around commas are ignored"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def show_session_buttons(update: Update, message: str = None) -> None:
    """Show session mode selection buttons."""
    keyboard = [
        [
            InlineKeyboardButton("➕ Add Absent", callback_data='add_absent'),
            InlineKeyboardButton("🆕 New Absent", callback_data='new_absent')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if message:
        await update.message.reply_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            "Choose your session mode:",
            reply_markup=reply_markup
        )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses for session mode selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'add_absent':
        # Continue with existing working file
        context.user_data['session_mode'] = 'add'
        
        if os.path.exists(config.EXCEL_WORKING_PATH):
            await query.edit_message_text(
                "✅ *Add Absent Mode*\n\n"
                "Continuing with existing working file.\n"
                "Send registration number endings (e.g., '1' or '1,3,5,7')",
                parse_mode='Markdown'
            )
        else:
            # No working file exists, create one from original
            shutil.copy(config.EXCEL_ORIGINAL_PATH, config.EXCEL_WORKING_PATH)
            await query.edit_message_text(
                "✅ *Add Absent Mode*\n\n"
                "Created new working file from original.\n"
                "Send registration number endings (e.g., '1' or '1,3,5,7')",
                parse_mode='Markdown'
            )
        
    elif query.data == 'new_absent':
        # Create fresh copy from original
        context.user_data['session_mode'] = 'new'
        shutil.copy(config.EXCEL_ORIGINAL_PATH, config.EXCEL_WORKING_PATH)
        
        await query.edit_message_text(
            "🆕 *New Absent Mode*\n\n"
            "Created fresh working file from original (all PRESENT).\n"
            "Send registration number endings (e.g., '1' or '1,3,5,7')",
            parse_mode='Markdown'
        )


def read_attendance_file():
    """Read the working attendance Excel file and return DataFrame."""
    try:
        if not os.path.exists(config.EXCEL_WORKING_PATH):
            # Create working file from original if it doesn't exist
            shutil.copy(config.EXCEL_ORIGINAL_PATH, config.EXCEL_WORKING_PATH)
        
        # Read with explicit string type for Registration Column to prevent precision loss
        df = pd.read_excel(config.EXCEL_WORKING_PATH, dtype={config.REGISTRATION_COLUMN: str})
        return df, None
    except FileNotFoundError:
        return None, "❌ Error: Original attendance file not found!"
    except Exception as e:
        return None, f"❌ Error reading file: {str(e)}"


def save_attendance_file(df):
    """Save the DataFrame back to working Excel file."""
    try:
        df.to_excel(config.EXCEL_WORKING_PATH, index=False)
        return True, None
    except Exception as e:
        return False, f"❌ Error saving file: {str(e)}"


def load_name_mapping():
    """Load the name list from Excel to map registration suffix to names."""
    try:
        if not os.path.exists(config.NAME_LIST_PATH):
            logger.error(f"Name list file not found at {config.NAME_LIST_PATH}")
            return {}

        # Read Excel file without header, as per inspection, force string to prevent float conversion
        df = pd.read_excel(config.NAME_LIST_PATH, header=None, dtype=str)
        
        mapping = {}
        # Iterate through rows
        for index, row in df.iterrows():
            # Based on inspection: Column 1 (index 1) has Reg No, Column 2 (index 2) has Name
            # Example Reg No: 2403727755921004 -> suffix '04'
            try:
                reg_col_val = str(row[1]).strip()
                name_col_val = str(row[2]).strip()
                
                # specific check for the header/empty rows
                if pd.isna(row[1]) or pd.isna(row[2]) or 'nan' in reg_col_val.lower():
                    continue
                    
                # Extract last 2 digits/chars
                suffix = reg_col_val[-2:]
                
                # Check if suffix is a number (to avoid headers)
                if suffix.isdigit():
                    mapping[suffix] = name_col_val
            except Exception as e:
                continue
                
        return mapping
    except Exception as e:
        logger.error(f"Error loading name mapping: {str(e)}")
        return {}


def generate_absentee_report(df):
    """Generate a formatted absentee text message."""
    try:
        # Load name mapping
        name_mapping = load_name_mapping()
        
        # Filter for ABSENT students
        absent_df = df[df[config.ATTENDANCE_COLUMN].astype(str).str.upper() == 'ABSENT'].copy()
        
        if absent_df.empty:
            return None
        
        absentees = []
        for _, row in absent_df.iterrows():
            reg_id = str(row[config.REGISTRATION_COLUMN]).replace('.0', '').strip()
            suffix = reg_id[-2:]
            
            # Lookup name, fallback to email user part if not found
            name = name_mapping.get(suffix, row[config.EMAIL_COLUMN].split('@')[0])
            absentees.append((suffix, name))
            
        # Sort by suffix
        absentees.sort(key=lambda x: x[0])
        
        # Format Date and Session
        now = datetime.now()
        date_str = now.strftime("%d-%m-%Y")
        hour = now.hour
        session = "FN" if hour < 13 else "AN"
        
        # Build Message
        message = f"{date_str} {session}\n"
        message += f"{config.CLASS_NAME}\n\n"
        message += "ABSENTEES:\n\n"
        
        for suffix, name in absentees:
            message += f"{suffix}-{name}\n"
            
        return message
    except Exception as e:
        return f"❌ Error generating report: {str(e)}"


async def handle_row_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle registration number suffix input from user (single or comma-separated)."""
    user_input = update.message.text.strip()
    
    # Check if user has selected a session mode
    if 'session_mode' not in context.user_data:
        keyboard = [
            [
                InlineKeyboardButton("➕ Add Absent", callback_data='add_absent'),
                InlineKeyboardButton("🆕 New Absent", callback_data='new_absent')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ Please choose a session mode first:",
            reply_markup=reply_markup
        )
        return
    
    # Parse numbers (comma-separated)
    numbers_str = [n.strip() for n in user_input.split(',')]
    
    # Validate all are numbers
    if not all(n.isdigit() for n in numbers_str):
        await update.message.reply_text(
            "⚠️ Please send valid numbers.\n"
            "Examples: '1' or '1,3,5,7' or '11,22,33'\n"
            "Use /help for more information."
        )
        return
    
    numbers = [n for n in numbers_str]
    
    # Read the Excel file
    df, error = read_attendance_file()
    if error:
        await update.message.reply_text(error)
        return
    
    # Convert registration IDs to strings and find matches
    df['Registration Id'] = df[config.REGISTRATION_COLUMN].astype(str).str.replace('.0', '', regex=False)
    
    # Find matching rows for each number
    updated_rows = []
    already_absent_rows = []
    not_found_numbers = []
    
    for number in numbers:
        # Pad single digit with 0 (e.g., '1' -> '01')
        if len(number) == 1:
            search_suffix = '0' + number
        else:
            search_suffix = number
        
        # Find rows where registration ID ends with this suffix
        matching_indices = df[df['Registration Id'].str.endswith(search_suffix)].index.tolist()
        
        if not matching_indices:
            not_found_numbers.append(number)
            continue
        
        # Process each matching row
        for df_index in matching_indices:
            email = df.loc[df_index, config.EMAIL_COLUMN]
            reg_id = df.loc[df_index, config.REGISTRATION_COLUMN]
            current_status = df.loc[df_index, config.ATTENDANCE_COLUMN]
            
            if current_status.upper() == 'ABSENT':
                already_absent_rows.append((number, email, reg_id))
            else:
                # Update attendance to ABSENT
                df.loc[df_index, config.ATTENDANCE_COLUMN] = 'ABSENT'
                updated_rows.append((number, email, reg_id))
    
    # Save the file if there were updates
    if updated_rows:
        success, error = save_attendance_file(df)
        if not success:
            await update.message.reply_text(error)
            return
    
    # Build confirmation message
    confirmation_parts = []
    
    if updated_rows:
        confirmation_parts.append(f"✅ *Marked {len(updated_rows)} student(s) as ABSENT:*\n")
        for number, email, reg_id in updated_rows:
            # Format registration ID properly
            reg_id_str = f"{int(reg_id)}" if isinstance(reg_id, float) else str(reg_id)
            confirmation_parts.append(f"  • [{number}] {email}")
            confirmation_parts.append(f"    Reg: {reg_id_str}")
    
    if already_absent_rows:
        confirmation_parts.append(f"\nℹ️ *Already absent:*")
        for number, email, reg_id in already_absent_rows:
            reg_id_str = f"{int(reg_id)}" if isinstance(reg_id, float) else str(reg_id)
            confirmation_parts.append(f"  • [{number}] {email}")
    
    if not_found_numbers:
        confirmation_parts.append(f"\n⚠️ *Not found:* {', '.join(not_found_numbers)}")
    
    if updated_rows:
        confirmation_parts.append("\n📎 Sending updated Excel file...")
        confirmation_message = "\n".join(confirmation_parts)
        await update.message.reply_text(confirmation_message, parse_mode='Markdown')
        
        # Send the updated Excel file
        try:
            await update.message.reply_document(
                document=open(config.EXCEL_WORKING_PATH, 'rb'),
                filename='Updated_Attendance.xlsx',
                caption=f"✅ Updated attendance file ({len(updated_rows)} student(s) marked as ABSENT)"
            )
            logger.info(f"Updated {len(updated_rows)} students: marked as ABSENT and file sent")
            
            # Show session buttons for next action
            # await show_session_buttons(update, "What would you like to do next?")
            
            # Generate and send absentee report
            report = generate_absentee_report(df)
            if report:
                await update.message.reply_text(report)
            
            await show_session_buttons(update, "What would you like to do next?")
            
        except Exception as e:
            await update.message.reply_text(f"⚠️ File updated but couldn't send: {str(e)}")
            logger.error(f"Error sending file: {str(e)}")
            # Show session buttons even on error
            await show_session_buttons(update, "What would you like to do next?")
    else:
        # No updates made
        if already_absent_rows or not_found_numbers:
            confirmation_message = "\n".join(confirmation_parts)
            await update.message.reply_text(confirmation_message, parse_mode='Markdown')
        else:
            await update.message.reply_text("ℹ️ No changes made.")
        
        # Generate and send absentee report so user sees current state
        report = generate_absentee_report(df)
        if report:
            await update.message.reply_text(report)

        # Show session buttons for next action
        await show_session_buttons(update, "What would you like to do next?")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error {context.error}")



def create_bot_application():
    """Create and configure the bot application."""
    # Check if bot token is configured
    if config.BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("❌ ERROR: Please set your bot token in config.py")
        print("Get your token from @BotFather on Telegram")
        return None
    
    # Check if original file exists
    if not os.path.exists(config.EXCEL_ORIGINAL_PATH):
        print(f"❌ ERROR: Original attendance file not found at:")
        print(f"   {config.EXCEL_ORIGINAL_PATH}")
        return None
    
    # Create the Application
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Register callback query handler for buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Register message handler for row numbers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_row_numbers))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    return application


# Global variable for the bot application (used in Render mode)
bot_app = None

# Define lifespan for FastAPI (startup/shutdown events)
@asynccontextmanager
async def lifespan(app: FastAPI):
    if bot_app:
        # Set webhook
        webhook_url = f"{os.getenv('RENDER_EXTERNAL_URL')}/telegram"
        logger.info(f"Setting webhook to: {webhook_url}")
        await bot_app.bot.set_webhook(url=webhook_url)
        
        # Start bot application
        async with bot_app:
            await bot_app.start()
            yield
            # Stop bot application on shutdown
            await bot_app.stop()
    else:
        yield


# Create FastAPI app if running on Render
if os.getenv('RENDER'):
    bot_app = create_bot_application()
    if bot_app:
        app = FastAPI(lifespan=lifespan)

        @app.get("/")
        async def health_check():
            """Keep-alive endpoint."""
            return {"status": "alive"}

        @app.post("/telegram")
        async def telegram_webhook(request: Request):
            """Handle incoming Telegram updates."""
            try:
                data = await request.json()
                update = Update.de_json(data, bot_app.bot)
                await bot_app.process_update(update)
                return Response(status_code=200)
            except Exception as e:
                logger.error(f"Error processing webhook: {e}")
                return Response(status_code=500)


def main() -> None:
    """Start the bot."""
    if os.getenv('RENDER'):
        # In Render, we rely on uvicorn running the 'app' object
        # This block is mainly for local testing if someone runs 'python bot.py' with RENDER=true
        port = int(os.getenv('PORT', 8000))
        print(f"🤖 Bot starting in WEBHOOK mode on port {port}...")
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        # Local polling mode
        print("🤖 Bot starting in POLLING mode...")
        application = create_bot_application()
        if application:
            print("Press Ctrl+C to stop")
            application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
