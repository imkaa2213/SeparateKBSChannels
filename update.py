import os
import requests

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

OUTPUT_DIR = "channels"

API = (
    "https://cfpwwwapi.kbs.co.kr/"
    "api/v1/landing/live/channel_code/{}"
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Referer": "https://onair.kbs.co.kr/",
}

# TV / video only — no radio.
#
# These codes correspond to the currently exposed KBS
# television/video channels.
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


# ---------------------------------------------------------
# Setup
# ---------------------------------------------------------

os.makedirs(OUTPUT_DIR, exist_ok=True)

session = requests.Session()
session.headers.update(HEADERS)

updated = 0
failed = 0


# ---------------------------------------------------------
# Retrieve each channel
# ---------------------------------------------------------

for channel in CHANNELS:

    code = channel["code"]
    name = channel["name"]
    filename = channel["file"]

    print(f"Updating {name} ({code})...")

    try:

        response = session.get(
            API.format(code),
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        items = data.get("channel_item", [])

        if not items:
            raise RuntimeError(
                "KBS API returned no channel_item"
            )

        # Find the first item containing a usable stream.
        stream_url = None

        for item in items:
            candidate = item.get("service_url")

            if candidate and ".m3u8" in candidate.lower():
                stream_url = candidate
                break

        if not stream_url:
            raise RuntimeError(
                "KBS API returned no HLS service_url"
            )

        # -------------------------------------------------
        # Build M3U
        # -------------------------------------------------

        playlist = (
            "#EXTM3U\n"
            f'#EXTINF:-1 tvg-id="{code}" '
            f'tvg-name="{name}" '
            f'group-title="KBS",{name}\n'
            f"#EXTVLCOPT:http-user-agent={USER_AGENT}\n"
            "#EXTVLCOPT:http-referrer="
            "https://onair.kbs.co.kr/\n"
            f"{stream_url}\n"
        )

        path = os.path.join(
            OUTPUT_DIR,
            filename,
        )

        # Write only after API retrieval succeeds.
        # Therefore an API failure will NOT destroy the
        # previously working playlist.
        with open(
            path,
            "w",
            encoding="utf-8",
        ) as file:
            file.write(playlist)

        updated += 1

        print(f"  OK -> {path}")

    except Exception as error:

        failed += 1

        print(
            f"  FAILED -> {name}: {error}"
        )


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

print()
print("=" * 50)
print(f"Updated: {updated}")
print(f"Failed : {failed}")
print("=" * 50)


# Don't let GitHub Actions report success if absolutely
# nothing could be refreshed.
if updated == 0:
    raise SystemExit(
        "ERROR: No KBS channels could be updated."
    )
