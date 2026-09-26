import json
import os
import sys
import urllib.request

SOURCE = (
    "https://raw.githubusercontent.com/"
    "kgkaku/KBS-Live-Channels-Playlist/"
    "main/kbs-nsplayer.m3u"
)

OUTPUT_DIR = "channels"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36"
)

# Only TV/video.
# Radio is not included.
CHANNELS = {
    "KBS1": {
        "code": "11",
        "file": "kbs1.m3u",
    },
    "KBS2": {
        "code": "12",
        "file": "kbs2.m3u",
    },
    "KBS World": {
        "code": "14",
        "file": "kbs-world.m3u",
    },
    "KBS24": {
        "code": "81",
        "file": "kbs24.m3u",
    },
    "KBS Drama": {
        "code": "N91",
        "file": "kbs-drama.m3u",
    },
    "KBS Joy": {
        "code": "N92",
        "file": "kbs-joy.m3u",
    },
    "KBS Life": {
        "code": "N93",
        "file": "kbs-life.m3u",
    },
    "KBS Story": {
        "code": "N94",
        "file": "kbs-story.m3u",
    },
    "KBS Kids": {
        "code": "N96",
        "file": "kbs-kids.m3u",
    },
}


def download_source():
    print("Downloading current KBS stream data...")

    request = urllib.request.Request(
        SOURCE,
        headers={
            "User-Agent": USER_AGENT,
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=30,
    ) as response:
        text = response.read().decode("utf-8")

    return json.loads(text)


def build_stream_url(link, cookie):
    """
    Source provides the stable stream URL separately
    from KBS's current signed authorization.

    For ordinary M3U players, append the authorization
    as the query string.
    """

    if not cookie:
        return link

    if "?" in link:
        return link + "&" + cookie

    return link + "?" + cookie


def write_channel(name, info, source_item):
    link = source_item.get("link", "").strip()
    cookie = source_item.get("cookie", "").strip()

    if not link:
        raise RuntimeError("Missing stream link")

    if not cookie:
        raise RuntimeError("Missing KBS authorization")

    stream_url = build_stream_url(
        link,
        cookie,
    )

    code = info["code"]

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
        info["file"],
    )

    # Write only after we have both URL and authorization.
    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:
        file.write(playlist)

    return path


def main():
    print()
    print("=" * 50)
    print(" KBS Separate Channel Updater")
    print("=" * 50)
    print()

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True,
    )

    try:
        source_data = download_source()
    except Exception as error:
        print(f"ERROR downloading source: {error}")
        return 1

    if not isinstance(source_data, list):
        print("ERROR: Source data isn't a JSON list.")
        return 1

    print(
        f"Source contains {len(source_data)} channels."
    )
    print()

    # Make source lookup by name.
    source_by_name = {}

    for item in source_data:
        if not isinstance(item, dict):
            continue

        name = item.get("name")

        if name:
            source_by_name[name.strip()] = item

    updated = 0
    failed = 0

    for name, info in CHANNELS.items():

        print("-" * 50)
        print(f"Channel : {name}")
        print(f"Code    : {info['code']}")

        source_item = source_by_name.get(name)

        if source_item is None:
            print("Result  : FAILED")
            print("Error   : Channel missing from source")
            failed += 1
            continue

        try:
            path = write_channel(
                name,
                info,
                source_item,
            )

            print(f"Result  : UPDATED")
            print(f"File    : {path}")

            updated += 1

        except Exception as error:
            print("Result  : FAILED")
            print(f"Error   : {error}")

            failed += 1

    print()
    print("=" * 50)
    print(" Update Summary")
    print("=" * 50)
    print(f"Updated: {updated}")
    print(f"Failed : {failed}")
    print("=" * 50)

    if updated == 0:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
