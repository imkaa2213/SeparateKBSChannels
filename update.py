import requests
import json
import re
import os

BASE = "https://onair.kbs.co.kr"
API = "https://cfpwwwapi.kbs.co.kr/api/v1/landing/live/channel_code/{}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/140 Safari/537.36"
    ),
    "Referer": "https://onair.kbs.co.kr/",
}

OUTPUT_DIR = "channels"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def safe_filename(name):
    name = re.sub(r'[\\/:*?"<>|]', "", name)
    name = re.sub(r"\s+", "-", name.strip())
    return name.lower()


# --------------------------------------------------
# 1. Download KBS On Air page
# --------------------------------------------------

print("Getting KBS channel list...")

html = requests.get(
    BASE,
    headers=HEADERS,
    timeout=30
).text


# --------------------------------------------------
# 2. Extract channelList
# --------------------------------------------------

match = re.search(
    r"var\s+channelList\s*=\s*JSON\.parse\('(.*?)'\);",
    html,
    re.DOTALL,
)

if not match:
    # Some KBS page versions use double quotes
    match = re.search(
        r'var\s+channelList\s*=\s*JSON\.parse\("(.*?)"\);',
        html,
        re.DOTALL,
    )

if not match:
    raise RuntimeError("Could not find KBS channelList")


raw = match.group(1)

raw = raw.replace('\\"', '"')
raw = raw.replace("\\'", "'")
raw = raw.replace("\\\\", "\\")

data = json.loads(raw)


# --------------------------------------------------
# 3. Find TV/video channels
# --------------------------------------------------

channels = []

for group in data.get("channel", []):

    for channel in group.get("channel_master", []):

        code = str(channel.get("channel_code", "")).strip()
        name = str(channel.get("title", "")).strip()
        channel_type = str(channel.get("channel_type", "")).upper()

        if not code or not name:
            continue

        # --------------------------
        # RADIO EXCLUDED HERE
        # --------------------------

        if channel_type != "TV":
            continue

        # Ignore regional duplicate codes such as
        # 10_21, 20_21 etc.
        #
        # Remove this condition if you later want
        # regional TV stations too.
        if "_" in code:
            continue

        channels.append({
            "code": code,
            "name": name,
        })


print(f"Found {len(channels)} TV/video channels")


# --------------------------------------------------
# 4. Get current stream URL
# --------------------------------------------------

for channel in channels:

    code = channel["code"]
    name = channel["name"]

    print()
    print(f"{name} [{code}]")

    try:

        api_url = API.format(code)

        response = requests.get(
            api_url,
            headers=HEADERS,
            timeout=30,
        )

        response.raise_for_status()

        api_data = response.json()

        items = api_data.get("channel_item", [])

        if not items:
            print("  No channel_item")
            continue

        stream_url = items[0].get("service_url")

        if not stream_url:
            print("  No service_url")
            continue


        # ------------------------------------------
        # Create filename
        # ------------------------------------------

        filename = safe_filename(name) + ".m3u"

        path = os.path.join(
            OUTPUT_DIR,
            filename
        )


        # ------------------------------------------
        # Generate M3U
        # ------------------------------------------

        playlist = f"""#EXTM3U
#EXTINF:-1 tvg-id="{code}" tvg-name="{name}" group-title="KBS",{name}
#EXTVLCOPT:http-referrer=https://onair.kbs.co.kr/
#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}
{stream_url}
"""


        # ------------------------------------------
        # Write file
        # ------------------------------------------

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(playlist)

        print(f"  ✓ {path}")


    except Exception as e:

        print(f"  ✗ Failed: {e}")
