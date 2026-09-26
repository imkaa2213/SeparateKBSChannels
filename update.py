import os
import re
import sys
import urllib.request

SOURCE = (
    "https://raw.githubusercontent.com/"
    "kgkaku/KBS-Live-Channels-Playlist/"
    "main/kbs-extvlcopt.m3u"
)

OUTPUT_DIR = "channels"

CHANNELS = {
    "11": "kbs1.m3u",
    "12": "kbs2.m3u",
    "14": "kbs-world.m3u",
    "81": "kbs24.m3u",
    "N91": "kbs-drama.m3u",
    "N92": "kbs-joy.m3u",
    "N93": "kbs-life.m3u",
    "N94": "kbs-story.m3u",
    "N96": "kbs-kids.m3u",
}


def download_playlist():
    print("Downloading current KBS playlist...")

    request = urllib.request.Request(
        SOURCE,
        headers={
            "User-Agent": "Mozilla/5.0",
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=30,
    ) as response:
        return response.read().decode(
            "utf-8",
            errors="replace",
        )


def parse_entries(text):
    """
    Split the upstream M3U into individual channel entries.
    """

    lines = text.splitlines()

    entries = []
    current = []

    for line in lines:

        line = line.strip()

        if line.startswith("#EXTINF:"):

            if current:
                entries.append(current)

            current = [line]

        elif current:

            # Keep VLC options and URL.
            if line:
                current.append(line)

                # Signed stream URL is the end of this entry.
                if (
                    not line.startswith("#")
                    and ".m3u8" in line.lower()
                ):
                    entries.append(current)
                    current = []

    if current:
        entries.append(current)

    return entries


def get_channel_code(entry):
    extinf = entry[0]

    match = re.search(
        r'tvg-id="([^"]+)"',
        extinf,
    )

    if not match:
        return None

    return match.group(1)


def get_stream_url(entry):
    for line in entry:

        if (
            not line.startswith("#")
            and ".m3u8" in line.lower()
        ):
            return line

    return None


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

    # ---------------------------------------------
    # Download upstream
    # ---------------------------------------------

    try:
        text = download_playlist()

    except Exception as error:

        print(
            f"ERROR downloading playlist: {error}"
        )

        return 1

    # ---------------------------------------------
    # Parse
    # ---------------------------------------------

    entries = parse_entries(text)

    print(
        f"Found {len(entries)} playlist entries."
    )

    print()

    updated = 0
    missing = []

    # ---------------------------------------------
    # Process channels
    # ---------------------------------------------

    for entry in entries:

        code = get_channel_code(entry)

        if not code:
            continue

        if code not in CHANNELS:
            continue

        stream_url = get_stream_url(entry)

        if not stream_url:
            print(
                f"SKIP {code}: no stream URL"
            )
            continue

        filename = CHANNELS[code]

        path = os.path.join(
            OUTPUT_DIR,
            filename,
        )

        # Preserve upstream entry exactly.
        output = (
            "#EXTM3U\n\n"
            + "\n".join(entry)
            + "\n"
        )

        with open(
            path,
            "w",
            encoding="utf-8",
        ) as file:

            file.write(output)

        updated += 1

        print(
            f"UPDATED {code:>3} -> {path}"
        )

    # ---------------------------------------------
    # Check expected channels
    # ---------------------------------------------

    for code, filename in CHANNELS.items():

        path = os.path.join(
            OUTPUT_DIR,
            filename,
        )

        if not os.path.exists(path):
            missing.append(code)

    # ---------------------------------------------
    # Summary
    # ---------------------------------------------

    print()
    print("=" * 50)
    print("Update Summary")
    print("=" * 50)

    print(
        f"Updated: {updated}"
    )

    if missing:

        print(
            "Missing: "
            + ", ".join(missing)
        )

    print("=" * 50)

    if updated == 0:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
