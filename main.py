import requests
import json
import time
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime

# --- CONFIGURATION ---
# Region can be GB, DE, US, ES, etc.
REGION = "GB"  
M3U_FILENAME = "rlaxx_playlist.m3u"
XML_FILENAME = "rlaxx_guide.xml"
# ---------------------

def get_data():
    session = requests.Session()
    
    # Advanced browser-mimicking headers to bypass 403 blocks 
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
        # Step 1: Login to generate a fresh token 
        print("Attempting to authenticate with Rlaxx API...")
        login_url = "https://rlaxx.zeasn.tv/livetv/api/device/browser/v1/device/login"
        login_payload = {
            "deviceId": str(uuid.uuid4()),
            "deviceModel": "web-browser",
            "appVersion": "1.0.0",
            "region": REGION
        }
        
        # Small delay to mimic human interaction
        time.sleep(2)
        
        login_res = session.post(login_url, json=login_payload, headers=browser_headers, timeout=20)
        login_res.raise_for_status()
        token = login_res.json().get('data', {}).get('token')
        
        if not token:
            print("Authentication successful, but no token was provided.")
            return

        # Update headers with the new session token
        session.headers.update({"token": token})

        # Step 2: Fetch all available channels
        print("Fetching channel list...")
        chan_res = session.get("https://rlaxx.zeasn.tv/livetv/api/device/browser/v1/channels", headers=browser_headers)
        channels = chan_res.json().get('data', [])

        if not channels:
            print("No channels found in the response.")
            return

        # Step 3: Build the M3U Playlist
        print(f"Creating {M3U_FILENAME}...")
        with open(M3U_FILENAME, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for ch in channels:
                ch_id = str(ch['id'])
                stream = ch.get('playUrl') or ch.get('url', "")
                logo = ch.get('logo', "")
                name = ch.get('name', "Unknown Channel")
                f.write(f'#EXTINF:-1 tvg-id="{ch_id}" tvg-logo="{logo}",{name}\n')
                f.write(f"{stream}\n")

        # Step 4: Build the XMLTV Guide
        print(f"Creating {XML_FILENAME}...")
        root = ET.Element("tv")
        all_ids = [str(ch['id']) for ch in channels]
        
        for ch in channels:
            c_node = ET.SubElement(root, "channel", id=str(ch['id']))
            ET.SubElement(c_node, "display-name").text = ch.get('name')
            if ch.get('logo'):
                ET.SubElement(c_node, "icon", src=ch.get('logo'))

        # Fetch EPG data in chunks of 30 to avoid API request limits
        start_time = int(time.time() * 1000)
        end_time = start_time + (24 * 60 * 60 * 1000)
        
        for i in range(0, len(all_ids), 30):
            chunk = all_ids[i:i+30]
            params = {"channelIds": ",".join(chunk), "startTime": start_time, "endTime": end_time}
            epg_res = session.get("https://rlaxx.zeasn.tv/livetv/api/device/browser/v1/epg", headers=browser_headers, params=params)
            
            for prog in epg_res.json().get('data', []):
                start_f = datetime.fromtimestamp(prog['startTime']/1000).strftime('%Y%m%d%H%M%S +0000')
                stop_f = datetime.fromtimestamp(prog['endTime']/1000).strftime('%Y%m%d%H%M%S +0000')
                p_node = ET.SubElement(root, "programme", start=start_f, stop=stop_f, channel=str(prog['channelId']))
                ET.SubElement(p_node, "title").text = prog.get('title')
                ET.SubElement(p_node, "desc").text = prog.get('description', '')

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(XML_FILENAME, encoding="utf-8", xml_declaration=True)

        print("Successfully generated all files.")

    except Exception as e:
        print(f"Workflow failed: {e}")

if __name__ == "__main__":
    get_data()
