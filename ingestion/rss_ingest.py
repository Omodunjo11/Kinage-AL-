"""
AL Ingestion — RSS Feed Pipeline
Sources: AARP, FTC, CFPB, Alzheimer's Association, NCOA
No PII risk — institutional public feeds only.

Run from ~/AL:
    python3 ingestion/rss_ingest.py

Requirements: pip install feedparser pyyaml
"""

import os
import re
import json
import yaml
import hashlib
import feedparser
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(BASE, "config/config.yaml")) as f:
    config = yaml.safe_load(f)

with open(os.path.join(BASE, config["taxonomy"]["path"].lstrip("./"))) as f:
    taxonomy = yaml.safe_load(f)

rss_cfg = config["ingestion"]["rss"]

def get_domain_tags(text: str) -> list[str]:
    text_l = text.lower()
    tags = []
    for name, domain in taxonomy["domains"].items():
        for sub in domain.get("subdomain", {}).values():
            if any(t.lower() in text_l for t in sub.get("triggers", [])):
                if name not in tags:
                    tags.append(name)
    return tags

def clean_html(text: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', text or '')
    return re.sub(r'\s+', ' ', text).strip()

def chunk_text(text: str, size: int = 400, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks, step = [], size - overlap
    for i in range(0, len(words), step):
        c = " ".join(words[i:i + size])
        if len(c.strip()) > 60:
            chunks.append(c)
    return chunks

def save_chunk(chunk: str, metadata: dict) -> str:
    out_dir = os.path.join(BASE, "corpus/external/rss")
    os.makedirs(out_dir, exist_ok=True)
    cid = hashlib.md5(chunk.encode()).hexdigest()[:12]
    record = {
        "id": cid,
        "text": chunk,
        "metadata": metadata,
        "ingested_at": datetime.utcnow().isoformat(),
    }
    with open(os.path.join(out_dir, f"{cid}.json"), "w") as f:
        json.dump(record, f, indent=2)
    return cid

def ingest_rss():
    stored = []

    for feed_info in rss_cfg["feeds"]:
        name = feed_info["name"]
        url = feed_info["url"]
        print(f"\n── {name} ──")

        feed = feedparser.parse(url)

        if feed.bozo:
            print(f"  ⚠ Parse warning: {feed.bozo_exception}")

        entries = feed.entries[:rss_cfg["max_items_per_feed"]]
        print(f"  {len(entries)} entries found")

        for entry in entries:
            title = entry.get("title", "")
            summary = clean_html(entry.get("summary", ""))
            content_list = entry.get("content", [])
            content = clean_html(content_list[0].get("value", "") if content_list else "")

            full_text = f"{title}\n\n{summary}\n\n{content}".strip()

            if len(full_text) < 100:
                continue

            tags = get_domain_tags(full_text)

            # Parse date safely
            try:
                pub_dt = datetime(*entry.published_parsed[:6]).isoformat() \
                    if hasattr(entry, "published_parsed") and entry.published_parsed \
                    else entry.get("published", "")
            except Exception:
                pub_dt = entry.get("published", "")

            meta = {
                "source": "rss",
                "feed_name": name,
                "feed_url": url,
                "title": title,
                "url": entry.get("link", ""),
                "published": pub_dt,
                "domain_tags": tags,
            }

            chunks = chunk_text(full_text)
            for chunk in chunks:
                cid = save_chunk(chunk, meta)
                stored.append(cid)

            print(f"  ✓ {title[:70]}")
            print(f"    tags: {tags} | {len(chunks)} chunk(s)")

    print(f"\n── RSS done: {len(stored)} chunks ──")
    return stored


if __name__ == "__main__":
    ingest_rss()
