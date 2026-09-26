import os
import sys
import requests

# =========================================================
# Configuration
# =========================================================

OUTPUT_DIR = "channels"

API = (
    "https://cfpwwwapi.kbs.co.kr/"
    "api/v1/landing/live/channel_code/{}"
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0.0.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Referer": "https://onair.kbs.co.kr/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

# ---------------------------------------------------------
# KBS TV / video channels
# Radio is intentionally excluded.
# ---------------------------------------------------------

CHANNELS = [
    {
        "code": "11",
        "name": "KBS1",
        "file": "kbs1.m3u",
    },
    {
        "code": "12",
        "name": "KBS2",
        "file": "kbs2.m3u",
    },
    {
        "code": "14",
        "name": "KBS World",
        "file": "kbs-world.m3u",
    },
    {
        "code": "81",
        "name": "KBS24",
        "file": "kbs24.m3u",
    },
    {
        "code": "N91",
        "name": "KBS Drama",
        "file": "kbs-drama.m3u",
    },
    {
        "code": "N92",
        "name": "KBS Joy",
        "file": "kbs-joy.m3u",
    },
    {
        "code": "N93",
        "name": "KBS Life",
        "file": "kbs-life.m3u",
    },
    {
        "code": "N94",
        "name": "KBS Story",
        "file": "kbs-story.m3u",
    },
    {
        "code": "N96",
        "name": "KBS Kids",
        "file": "kbs-kids.m3u",
    },
]


# =========================================================
# Helpers
# =========================================================

def get_items(data):
    """
    KBS has used more than one JSON structure.

    Try all known structures.
    """

    # Structure:
    #
    # {
    #   "channel": {
    #       "item": [...]
    #   }
    # }

    channel = data.get("channel")

    if isinstance(channel, dict):
        items = channel.get("item")

        if isinstance(items, list):
            return items

        if isinstance(items, dict):
            return [items]

    # Structure:
    #
    # {
    #   "channel_item": [...]
    # }

    items = data.get("channel_item")

    if isinstance(items, list):
        return items

    if isinstance(items, dict):
        return [items]

    # Occasionally an API may simply return:
    #
    # {
    #   "item": [...]
    # }

    items = data.get("item")

    if isinstance(items, list):
        return items

    if isinstance(items, dict):
        return [items]

    return []


def find_service_url(items):
    """
    Find the first usable service_url.
    """

    # Prefer HLS URLs.

    for item in items:

        if not isinstance(item, dict):
            continue

        url = item.get("service_url")

        if (
            isinstance(url, str)
            and url
            and ".m3u8" in url.lower()
        ):
            return url

    # If KBS returns something without ".m3u8",
    # accept service_url anyway.

    for item in items:

        if not isinstance(item, dict):
            continue

        url = item.get("service_url")

        if isinstance(url, str) and url:
            return url

    return None


def create_playlist(code, name, stream_url):
    """
    Create an M3U containing one KBS channel.
    """

    return (
        "#EXTM3U\n"
        f'#EXTINF:-1 '
        f'tvg-id="{code}" '
        f'tvg-name="{name}" '
        f'group-title="KBS",{name}\n'
        f"#EXTVLCOPT:http-user-agent={USER_AGENT}\n"
        "#EXTVLCOPT:http-referrer="
        "https://onair.kbs.co.kr/\n"
        f"{stream_url}\n"
    )


# =========================================================
# Start
# =========================================================

print()
print("==========================================")
print(" KBS TV Stream Updater")
print("==========================================")
print()

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True,
)

session = requests.Session()

session.headers.update(
    HEADERS
)

updated = 0
failed = 0


# =========================================================
# Update channels
# =========================================================

for channel in CHANNELS:

    code = channel["code"]
    name = channel["name"]
    filename = channel["file"]

    print("------------------------------------------")
    print(f"Channel : {name}")
    print(f"Code    : {code}")

    url = API.format(code)

    print(f"Request : {url}")

    try:

        # -------------------------------------------------
        # Request KBS API
        # -------------------------------------------------

        response = session.get(
            url,
            timeout=30,
        )

        print(
            f"HTTP    : {response.status_code}"
        )

        response.raise_for_status()

        # -------------------------------------------------
        # Parse JSON
        # -------------------------------------------------

        try:

            data = response.json()

        except Exception:

            preview = response.text[:500]

            raise RuntimeError(
                "KBS returned non-JSON response: "
                + preview
            )

        # -------------------------------------------------
        # Locate channel items
        # -------------------------------------------------

        items = get_items(data)

        if not items:

            # Print the top-level keys because this is
            # extremely useful if KBS changes its API.

            keys = list(data.keys())

            raise RuntimeError(
                "Could not locate channel items. "
                f"Top-level JSON keys: {keys}. "
                f"Response: {str(data)[:1000]}"
            )

        print(
            f"Items   : {len(items)}"
        )

        # -------------------------------------------------
        # Find stream
        # -------------------------------------------------

        stream_url = find_service_url(
            items
        )

        if not stream_url:

            raise RuntimeError(
                "No service_url found. "
                f"Items: {str(items)[:1000]}"
            )

        print(
            "Stream  : found"
        )

        # -------------------------------------------------
        # Generate M3U
        # -------------------------------------------------

        playlist = create_playlist(
            code,
            name,
            stream_url,
        )

        filepath = os.path.join(
            OUTPUT_DIR,
            filename,
        )

        # IMPORTANT:
        #
        # We don't touch the old file until a new stream
        # URL has successfully been obtained.
        #
        # Therefore a temporary KBS API failure won't
        # destroy the previous playlist.

        with open(
            filepath,
            "w",
            encoding="utf-8",
        ) as file:

            file.write(
                playlist
            )

        updated += 1

        print(
            f"Result  : UPDATED -> {filepath}"
        )

    except Exception as error:

        failed += 1

        print(
            f"Result  : FAILED"
        )

        print(
            f"Error   : {error}"
        )

    print()


# =========================================================
# Summary
# =========================================================

print()
print("==========================================")
print(" Update Summary")
print("==========================================")
print()

print(
    f"Updated: {updated}"
)

print(
    f"Failed : {failed}"
)

print()


# =========================================================
# Exit status
# =========================================================

if updated == 0:

    print(
        "ERROR: No KBS channels were updated."
    )

    sys.exit(1)


if failed > 0:

    print(
        "WARNING: Some channels failed, but successful "
        "channels were updated."
    )

    # Don't fail the entire GitHub Action if at least
    # one channel succeeded.
    sys.exit(0)


print(
    "All available KBS channels updated successfully."
)

sys.exit(0)
