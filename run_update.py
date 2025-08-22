import os
import sys
import shutil
import subprocess
import time

def main():
    if len(sys.argv) < 2:
        print("No target executable provided.")
        sys.exit(1)

    target_exe = sys.argv[1]  # e.g., "main.exe"
    temp_file = target_exe + ".new"  # e.g., "main.exe.new"

    # Wait until the main app fully closes
    time.sleep(2)

    # Replace old exe with the new one
    try:
        if os.path.exists(temp_file):
            shutil.move(temp_file, target_exe)
            print(f"Replaced {target_exe} with the new version.")
        else:
            print("No new version file found.")
            sys.exit(1)
    except Exception as e:
        print(f"Update failed: {e}")
        sys.exit(1)

    # Restart the updated app
    try:
        subprocess.Popen([target_exe])
        print("Restarted the updated app.")
    except Exception as e:
        print(f"Could not restart app: {e}")

if __name__ == "__main__":
    main()
