import requests
import json
import time
import uuid
import xml.etree.ElementTree as ET
import os
from datetime import datetime

# --- CONFIGURATION ---
REGION = "GB" 
M3U_FILENAME = "rlaxx_playlist.m3u"
XML_FILENAME = "rlaxx_guide.xml"

def get_session_token():
    init_url = "https://rlaxx.zeasn.tv/livetv/api/device/browser/v1/device/login"
    payload = {
        "deviceId": str(uuid.uuid4()),
        "deviceModel": "web-browser",
        "appVersion": "1.0.0",
        "region": REGION
    }
    # These extra headers help bypass 403 blocks on GitHub Actions
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Referer": "https://watch.whaletvplus.com/",
        "Origin": "https://watch.whaletvplus.com"
    }
    try:
        response = requests.post(init_url, json=payload, headers=headers, timeout=20)
        response.raise_for_status()
        return response.json().get('data', {}).get('token')
    except Exception as e:
        print(f"Auth Error: {e}")
        return None

def run_sync():
    token = get_session_token()
    if not token:
        return

    base_url = "https://rlaxx.zeasn.tv/livetv/api/device/browser/v1"
    headers = {"token": token, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    try:
        # Fetch Channels
        chan_res = requests.get(f"{base_url}/channels", headers=headers, timeout=20)
        channels = chan_res.json().get('data', [])
        
        if not channels:
            print("No channels found. Skipping file creation.")
            return

        # Generate M3U
        with open(M3U_FILENAME, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for ch in channels:
                f.write(f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-logo="{ch.get("logo","")}",{ch.get("name")}\n')
                f.write(f"{ch.get('playUrl') or ch.get('url','')}\n")

        # Generate XMLTV
        root = ET.Element("tv")
        # ... (Include the XML generation logic from the previous step)
        tree = ET.ElementTree(root)
        tree.write(XML_FILENAME, encoding="utf-8", xml_declaration=True)
        
        print("Files generated successfully.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_sync()
