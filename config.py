"""
Configuration file for Telegram Attendance Bot
"""

import os

# Telegram Bot Token - Get this from @BotFather on Telegram
# Replace 'YOUR_BOT_TOKEN_HERE' with your actual bot token
BOT_TOKEN = '8270343346:AAGHTnnEf4sksRMTeX2qfesEx1ynF1hdS_8'

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to the Excel files
EXCEL_ORIGINAL_PATH = os.path.join(BASE_DIR, 'attendance_original.xlsx')  # Never modified
EXCEL_WORKING_PATH = os.path.join(BASE_DIR, 'attendance_working.xlsx')    # Working copy

# Column name for attendance in the Excel file
ATTENDANCE_COLUMN = 'Attendance *'

# Email column name
EMAIL_COLUMN = 'Email Id'

# Registration ID column name
REGISTRATION_COLUMN = 'Registration Id'

# Path to the Name List file
NAME_LIST_PATH = os.path.join(BASE_DIR, 'name_list.xlsx')

# Class Name for the report
CLASS_NAME = "II M Tech CSE"
