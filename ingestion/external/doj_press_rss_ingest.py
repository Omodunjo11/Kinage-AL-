"""
DOJ Press Ingest — Latest Releases (Correct Date Handling)
"""

import requests
import json
import hashlib
import re
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent.parent
OUTPUT_DIR = BASE / "corpus" / "external" / "rss"

DOJ_API_URL = "https://www.justice.gov/api/v1/press_releases.json"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def extract_changed_datetime(changed_field: str) -> str:
    """
    Extract ISO datetime from DOJ <time datetime="..."> field.
    """
    if not changed_field:
        return datetime.utcnow().isoformat()

    match = re.search(r'datetime="([^"]+)"', changed_field)
    if match:
        return match.group(1)

    return datetime.utcnow().isoformat()

def save_chunk(title, link, published, summary):
    chunk_id = hashlib.md5(link.encode()).hexdigest()[:12]

    data = {
        "id": chunk_id,
        "text": summary,
        "metadata": {
            "source": "doj_api",
            "title": title,
            "url": link,
            "published": published,
            "domain_tags": [],
        },
        "ingested_at": datetime.utcnow().isoformat(),
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_DIR / f"{chunk_id}.json", "w") as f:
        json.dump(data, f, indent=2)

def main():
    print("── DOJ API Ingest (Latest Releases) ──")

    # Step 1: Get metadata to calculate last page
    initial_response = requests.get(DOJ_API_URL, headers=HEADERS)

    if initial_response.status_code != 200:
        print("Initial request failed:", initial_response.status_code)
        return

    meta = initial_response.json()

    total_count = int(meta["metadata"]["resultset"]["count"])
    page_size = int(meta["metadata"]["resultset"]["pagesize"])

    last_page = total_count // page_size

    print("Total releases:", total_count)
    print("Fetching page:", last_page)

    # Step 2: Fetch latest page
    params = {"page": last_page}
    response = requests.get(DOJ_API_URL, headers=HEADERS, params=params)

    if response.status_code != 200:
        print("Latest page fetch failed:", response.status_code)
        return

    data = response.json()
    entries = data.get("results", [])

    print("Entries found:", len(entries))

    count = 0

    for entry in entries:
        title = entry.get("title", "")
        link = entry.get("url", "")
        summary = entry.get("body", "")

        changed_raw = entry.get("changed", "")
        published = extract_changed_datetime(changed_raw)

        if not link or not title:
            continue

        save_chunk(title, link, published, summary)
        count += 1

    print(f"{count} DOJ articles saved")

if __name__ == "__main__":
    main()
