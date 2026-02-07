
import pandas as pd
import config
import os

def check_attendance_values():
    path = config.EXCEL_ORIGINAL_PATH
    print(f"Checking {path}")
    try:
        df = pd.read_excel(path, dtype={config.REGISTRATION_COLUMN: str})
        if config.ATTENDANCE_COLUMN in df.columns:
            unique_vals = df[config.ATTENDANCE_COLUMN].unique()
            print(f"Unique values in '{config.ATTENDANCE_COLUMN}': {unique_vals}")
        else:
            print(f"Column '{config.ATTENDANCE_COLUMN}' not found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_attendance_values()
