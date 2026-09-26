import os
import requests

CHANNELS = {
    "N91": {
        "name": "KBS N Sports",
        "file": "kbs-n-sports.m3u",
    },
    "N92": {
        "name": "KBS Joy",
        "file": "kbs-joy.m3u",
    },
    "N93": {
        "name": "KBS Drama",
        "file": "kbs-drama.m3u",
    },
}

API = "https://cfpwwwapi.kbs.co.kr/api/v1/landing/live/channel_code/{}"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://onair.kbs.co.kr/",
}

os.makedirs("channels", exist_ok=True)

for code, channel in CHANNELS.items():

    name = channel["name"]
    filename = channel["file"]

    try:
        r = requests.get(
            API.format(code),
            headers=HEADERS,
            timeout=15,
        )

        r.raise_for_status()
        data = r.json()

        stream_url = data["channel_item"][0]["service_url"]

        playlist = f"""#EXTM3U
#EXTINF:-1 tvg-id="{code}" tvg-name="{name}" group-title="KBS",{name}
#EXTVLCOPT:http-referrer=https://onair.kbs.co.kr/
#EXTVLCOPT:http-user-agent=Mozilla/5.0
{stream_url}
"""

        path = os.path.join("channels", filename)

        with open(path, "w", encoding="utf-8") as f:
            f.write(playlist)

        print(f"✓ Updated {name}")
        print(f"  {path}")

    except Exception as e:
        print(f"✗ Failed {name}: {e}")
