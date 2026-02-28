import feedparser
import requests
from pprint import pprint

def validate_feed(url: str):
    print(f"\nTesting: {url}")

    # First: raw HTTP check
    try:
        r = requests.get(
            url,
            headers={"User-Agent": "AL-Research-Agent/1.0"},
            timeout=10
        )
        print("HTTP Status:", r.status_code)
    except Exception as e:
        print("HTTP Error:", e)
        return

    # Second: feedparser check
    feed = feedparser.parse(
        url,
        request_headers={"User-Agent": "AL-Research-Agent/1.0"}
    )

    print("Bozo:", feed.bozo)
    print("Entries:", len(feed.entries))
    print("Feed Title:", getattr(feed.feed, "title", None))

    if feed.bozo:
        print("Bozo Exception:", getattr(feed, "bozo_exception", None))

    if feed.entries:
        print("First Entry Title:", feed.entries[0].get("title"))

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python validate_feed.py <RSS_URL>")
    else:
        validate_feed(sys.argv[1])
