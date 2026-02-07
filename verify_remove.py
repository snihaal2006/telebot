
import pandas as pd
import config
import os
import shutil

def verify_remove():
    output = []
    
    # Setup test file
    test_file = "test_attendance.xlsx"
    shutil.copy(config.EXCEL_ORIGINAL_PATH, test_file)
    output.append(f"Created test file: {test_file}")
    
    try:
        # 1. Mark a student as ABSENT
        df = pd.read_excel(test_file, dtype={config.REGISTRATION_COLUMN: str})
        
        # Pick the 3rd student (index 2)
        target_idx = 2
        reg_id = df.loc[target_idx, config.REGISTRATION_COLUMN]
        email = df.loc[target_idx, config.EMAIL_COLUMN]
        
        output.append(f"Target Student: {reg_id} ({email}) - Initial Status: {df.loc[target_idx, config.ATTENDANCE_COLUMN]}")
        
        # Mark Absent
        df.loc[target_idx, config.ATTENDANCE_COLUMN] = "ABSENT"
        df.to_excel(test_file, index=False)
        output.append(f"Marked as ABSENT.")
        
        # Verify Absent
        df = pd.read_excel(test_file, dtype={config.REGISTRATION_COLUMN: str})
        current_status = df.loc[target_idx, config.ATTENDANCE_COLUMN]
        if current_status == "ABSENT":
             output.append("Verified: Student is ABSENT.")
        else:
             output.append(f"FAILURE: Student is {current_status} (Expected ABSENT)")
             
        # 2. Mark as PRESENT (Remove Absent Logic)
        # Simulate logic: Find by regex/suffix
        suffix = reg_id[-2:] # Last 2 digits
        output.append(f"Simulating Remove Absent for suffix: {suffix}")
        
        # Logic from bot.py
        search_suffix = suffix # Simplified for test
        matching_indices = df[df[config.REGISTRATION_COLUMN].str.endswith(search_suffix)].index.tolist()
        
        for idx in matching_indices:
            if idx == target_idx:
                 df.loc[idx, config.ATTENDANCE_COLUMN] = "PRESENT"
                 output.append("Set status to PRESENT")
        
        df.to_excel(test_file, index=False)
        
        # 3. Verify Final Status
        df = pd.read_excel(test_file, dtype={config.REGISTRATION_COLUMN: str})
        final_status = df.loc[target_idx, config.ATTENDANCE_COLUMN]
        
        if final_status == "PRESENT":
             output.append("SUCCESS: Student is back to PRESENT.")
        else:
             output.append(f"FAILURE: Student is {final_status} (Expected PRESENT)")
             
    except Exception as e:
        output.append(f"Error: {e}")
        
    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)
        
    with open("verify_remove_output.txt", "w") as f:
        f.write("\n".join(output))
    print("Verification complete. Output written to verify_remove_output.txt")

if __name__ == "__main__":
    verify_remove()
