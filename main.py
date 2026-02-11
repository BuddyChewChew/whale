import requests
import json
import time
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime

# --- CONFIGURATION ---
REGION = "GB"  
M3U_FILENAME = "rlaxx_playlist.m3u"
XML_FILENAME = "rlaxx_guide.xml"

def get_data():
    session = requests.Session()
    
    # These headers are the "secret sauce" to bypass the 403 block
    browser_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://watch.whaletvplus.com",
        "Referer": "https://watch.whaletvplus.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "Connection": "keep-alive"
    }

    try:
        # Step 1: Login to get the token
        print("Logging in to get fresh token...")
        login_url = "https://rlaxx.zeasn.tv/livetv/api/device/browser/v1/device/login"
        login_payload = {
            "deviceId": str(uuid.uuid4()),
            "deviceModel": "web-browser",
            "appVersion": "1.0.0",
            "region": REGION
        }
        
        login_res = session.post(login_url, json=login_payload, headers=browser_headers, timeout=20)
        login_res.raise_for_status()
        token = login_res.json().get('data', {}).get('token')
        
        if not token:
            print("Login successful but no token found in response.")
            return

        # Update session with the new token
        session.headers.update({"token": token})

        # Step 2: Fetch Channels
        print("Fetching channel list...")
        chan_res = session.get("https://rlaxx.zeasn.tv/livetv/api/device/browser/v1/channels", headers=browser_headers)
        channels = chan_res.json().get('data', [])

        if not channels:
            print("No channels found.")
            return

        # Step 3: Generate M3U
        print(f"Generating {M3U_FILENAME}...")
        with open(M3U_FILENAME, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for ch in channels:
                f.write(f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-logo="{ch.get("logo","")}",{ch.get("name")}\n')
                f.write(f"{ch.get('playUrl') or ch.get('url','')}\n")

        # Step 4: Generate XMLTV
        print(f"Generating {XML_FILENAME}...")
        root = ET.Element("tv")
        # (Shortened for brevity - reuse your previous XML logic here)
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(XML_FILENAME, encoding="utf-8", xml_declaration=True)

        print("Done! Both files created.")

    except Exception as e:
        print(f"Failed to fetch data: {e}")

if __name__ == "__main__":
    run_data_sync = get_data()
