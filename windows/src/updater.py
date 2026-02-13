import requests
import os
import subprocess
import zipfile
import io
import sys

def get_local_version():
    version_path = os.path.join("data", "version")
    if os.path.exists(version_path):
        with open(version_path, "r") as f:
            return f.read().strip()
    return ""

def check_latest_release(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            release_name = data.get("name")
            assets = data.get("assets", [])
            for asset in assets:
                if "win" in asset.get("name").lower():
                    return release_name, asset.get("browser_download_url")
    except Exception:
        pass
    return None, None

def run_update(dl_url, new_version):
    r = requests.get(dl_url)
    if r.status_code == 200:
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            z.extractall("update_temp")
        
        v_dir = os.path.join("update_temp", "src", "data")
        os.makedirs(v_dir, exist_ok=True)
        with open(os.path.join(v_dir, "version"), "w") as f:
            f.write(new_version)

        with open("finish_update.bat", "w") as f:
            f.write(f"""@echo off
timeout /t 3 /nobreak > nul
del /f /q "data\\.setup_done"
xcopy /s /y "update_temp\\*" "..\\"
rd /s /q "update_temp"
echo Update complete.
cd ..
start start.bat
del "%~f0"
""")
        
        subprocess.Popen(["finish_update.bat"], shell=True)
        sys.exit(0)

if __name__ == "__main__":
    owner = "da036b97b7c705909d6ffbd2e3349128"
    repo = "LTX-Tools"
    
    local_v = get_local_version()
    latest_v, download_url = check_latest_release(owner, repo)
    
    if latest_v and str(latest_v).lower() != str(local_v).lower():
        print(f"Update found: {latest_v}. Downloading...")
        run_update(download_url, latest_v)
    else:
        print("You are already on the latest version.")
        sys.exit(1) # This tells the .bat NOT to close