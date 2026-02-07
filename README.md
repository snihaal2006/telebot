# Telegram Attendance Bot

A Telegram bot that allows you to mark students as absent in an Excel attendance sheet by simply sending row numbers.

## Features

- ✅ **Match by registration number** - Send last digits of reg numbers
- 🔢 **Multiple students** - Send comma-separated numbers (e.g., "1,3,5,7")
- 🔄 **Auto-padding** - Single digit '1' matches reg ending in '01'
- 🛡️ **Original file protected** - Never modifies the original Excel file
- 📊 **Session modes**:
  - **Add Absent** - Continue editing existing working file
  - **New Absent** - Start fresh from original (all PRESENT)
- 📎 Sends edited Excel file back to you
- 🔍 Validates row numbers
- ℹ️ Shows student details on update
- ⚠️ Prevents duplicate updates

## Setup

### 1. Create a Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token you receive

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the Bot

1. Open `config.py`
2. Replace `'YOUR_BOT_TOKEN_HERE'` with your actual bot token from BotFather
3. Verify the Excel file path is correct (default: `C:\Users\Nihaal S\Downloads\Upload_Attendance (1).xlsx`)

### 4. Run the Bot

```bash
python bot.py
```

## Usage

1. Start a chat with your bot on Telegram
2. Send `/start` to see the welcome message
3. Choose session mode:
   - **➕ Add Absent** - Continue with existing working file
   - **🆕 New Absent** - Start fresh from original
4. Send registration number endings:
   - Single digit: `1` (matches reg ending in 01)
   - Double digit: `11` (matches reg ending in 11)
   - Multiple: `1,3,5,7` or `11,22,33`
5. Receive the updated Excel file

### Commands

- `/start` - Start the bot and choose session mode
- `/help` - Show help information

### How Registration Matching Works

The bot matches students by the **last 2 digits** of their registration number:
- Input `1` → Auto-padded to `01` → Matches reg numbers ending in `01`
- Input `11` → Matches reg numbers ending in `11`
- Input `1,3,5` → Matches reg numbers ending in `01`, `03`, `05`

### Session Modes

**Add Absent Mode**
- Continues editing the existing working file
- Preserves previous changes
- Use when adding more absent students to current session

**New Absent Mode**
- Creates a fresh copy from the original file
- All students start as PRESENT
- Use when starting a new attendance session

### Example

```
You: /start
Bot: 👋 Welcome to the Attendance Bot!
     [Shows session mode buttons: Add Absent | New Absent]

You: [Click "New Absent"]
Bot: 🆕 New Absent Mode
     Created fresh working file from original (all PRESENT).
     Send registration number endings (e.g., '1' or '1,3,5,7')

You: 1,3,5
Bot: ✅ Marked 3 student(s) as ABSENT:
       • [1] student1@skcet.ac.in
         Reg: 240372775592101
       • [3] student3@skcet.ac.in
         Reg: 240372775592103
       • [5] student5@skcet.ac.in
         Reg: 240372775592105
     
     📎 Sending updated Excel file...
     
Bot: [Sends Updated_Attendance.xlsx file]
     ✅ Updated attendance file (3 student(s) marked as ABSENT)
```

## File Structure

```
telebot/
├── bot.py              # Main bot application
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Notes

- Row numbers start from 1 (excluding the header row)
- Make sure the Excel file is not open when the bot runs
- The bot will prevent marking already absent students again
- All updates are logged to the console

## Troubleshooting

**Bot doesn't start:**
- Check if you've set the correct bot token in `config.py`
- Verify all dependencies are installed

**File not found error:**
- Check the Excel file path in `config.py`
- Make sure the file exists at the specified location

**Permission error:**
- Close the Excel file if it's open
- Check file permissions
