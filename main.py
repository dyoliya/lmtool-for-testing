import os
import requests
import shutil
import subprocess
import sys
from dotenv import load_dotenv
from interface.display import main as start_ui

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

dotenv_path = resource_path(os.path.join("misc", ".env"))

load_dotenv(dotenv_path)

# Replace these with your repository details
GITHUB_USER = os.getenv("GITHUB_USER_NEW")
GITHUB_REPO = os.getenv("GITHUB_REPO_NEW")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN_NEW")
GITHUB_API_URL = f'https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest'
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

def get_latest_release():
    response = requests.get(GITHUB_API_URL, headers=HEADERS if GITHUB_TOKEN else None)
    if response.status_code == 200:
        release_data = response.json()
        version = release_data['tag_name']
        for asset in release_data['assets']:
            if asset['name'] == 'main.exe':
                download_url = asset['browser_download_url']
                return version, download_url
    return None, None

def download_new_version(download_url):
    """Download new version to a temporary file (main.exe.new)."""
    new_file = "main.exe.new"
    with requests.get(download_url, stream=True) as r:
        with open(new_file, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
    print("Tool update downloaded successfully!")

def check_for_updates():
    local_version = open('version.txt').read().strip()
    latest_version, download_url = get_latest_release()

    print(f"Lead Management Tools {local_version}")

    if latest_version and local_version != latest_version:
        print(f"New Tool Version available: {latest_version}\nDownloading...")
        download_new_version(download_url)

        # Update the version.txt file with the latest version
        with open('version.txt', 'w') as version_file:
            version_file.write(latest_version)

        return True
    else:
        return False

def run_updater():
    updater_path = "update/run_update.exe"
    if not os.path.exists(updater_path):
        print("Updater not found! Please reinstall the tool.")
        sys.exit(1)

    subprocess.Popen([updater_path, "main.exe"])
    sys.exit()

def create_directories() -> None:

    directories = [
        './data',
        './data/pipedrive',
        './data/tz_file',
        './data/c3_files',
        './data/c3_files/contact_skip_traced_addresses',
        './data/c3_files/contact_addresses',
        './data/c3_files/contact_email_addresses',
        './data/c3_files/contact_phone_numbers',
        './data/c3_files/contacts'
        ]
    
    for dir in directories:
        os.makedirs(dir, exist_ok=True)


def main():

    if check_for_updates():
        run_updater()
    else:
        create_directories()
        start_ui()

if __name__ == "__main__":
    main()
