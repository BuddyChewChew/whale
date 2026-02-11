import requests
import json
import time
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime

# --- CONFIGURATION ---
REGION = "GB"  # Change to DE, US, ES, etc., depending on your needs
M3U_FILENAME = "rlaxx_playlist.m3u"
XML_FILENAME = "rlaxx_guide.xml"
# ---------------------

def get_session_token():
    """Generates a fresh guest session token dynamically."""
    init_url = "https://rlaxx.zeasn.tv/livetv/api/device/browser/v1/device/login"
    payload = {
        "deviceId": str(uuid.uuid4()),
        "deviceModel": "web-browser",
        "appVersion": "1.0.0",
        "region": REGION
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(init_url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json().get('data', {}).get('token')
    except Exception as e:
        print(f"Auth Error: {e}")
        return None

def format_date(ms):
    """Converts millisecond timestamp to XMLTV format."""
    return datetime.fromtimestamp(ms / 1000.0).strftime('%Y%m%d%H%M%S +0000')

def run_sync():
    token = get_session_token()
    if not token:
        print("Failed to authenticate with Rlaxx API.")
        return

    base_url = "https://rlaxx.zeasn.tv/livetv/api/device/browser/v1"
    headers = {
        "token": token,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Origin": "https://watch.whaletvplus.com",
        "Referer": "https://watch.whaletvplus.com/"
    }

    try:
        # 1. Fetch Channels
        print("Fetching channels...")
        chan_res = requests.get(f"{base_url}/channels", headers=headers, timeout=15)
        channels = chan_res.json().get('data', [])

        # 2. Build M3U
        print(f"Creating {M3U_FILENAME}...")
        with open(M3U_FILENAME, "w", encoding="utf-8") as f:
            f.write(f'#EXTM3U x-tvg-url="https://raw.githubusercontent.com/${{GITHUB_REPOSITORY}}/main/{XML_FILENAME}"\n')
            for ch in channels:
                ch_id = str(ch['id'])
                stream_url = ch.get('playUrl') or ch.get('url', "")
                logo = ch.get('logo', "")
                name = ch.get('name', "Unknown")
                f.write(f'#EXTINF:-1 tvg-id="{ch_id}" tvg-logo="{logo}",{name}\n')
                f.write(f"{stream_url}\n")

        # 3. Build XMLTV
        print("Creating XMLTV Guide...")
        root = ET.Element("tv")
        all_ids = []
        for ch in channels:
            ch_id = str(ch['id'])
            all_ids.append(ch_id)
            c_node = ET.SubElement(root, "channel", id=ch_id)
            ET.SubElement(c_node, "display-name").text = ch.get('name')
            if ch.get('logo'):
                ET.SubElement(c_node, "icon", src=ch.get('logo'))

        # Fetch EPG in chunks
        start_time = int(time.time() * 1000)
        end_time = start_time + (24 * 60 * 60 * 1000)
        
        for i in range(0, len(all_ids), 30):
            chunk = all_ids[i:i+30]
            params = {"channelIds": ",".join(chunk), "startTime": start_time, "endTime": end_time}
            epg_res = requests.get(f"{base_url}/epg", headers=headers, params=params, timeout=15)
            
            for prog in epg_res.json().get('data', []):
                p_node = ET.SubElement(root, "programme", 
                                      start=format_date(prog['startTime']), 
                                      stop=format_date(prog['endTime']), 
                                      channel=str(prog['channelId']))
                ET.SubElement(p_node, "title").text = prog.get('title')
                ET.SubElement(p_node, "desc").text = prog.get('description', '')
            print(f"Processed chunk {i//30 + 1}")

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(XML_FILENAME, encoding="utf-8", xml_declaration=True)

        print("Finished successfully.")

    except Exception as e:
        print(f"Error during execution: {e}")

if __name__ == "__main__":
    run_sync()
