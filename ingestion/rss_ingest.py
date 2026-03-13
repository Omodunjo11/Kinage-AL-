"""
AL Ingestion — RSS Feed Pipeline
Google News–based RSS ingestion with platform tagging.

Run:
    python ingestion/rss_ingest.py
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


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

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
    chunks = []
    step = size - overlap

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


# ─────────────────────────────────────────────
# Main Ingestion
# ─────────────────────────────────────────────

def ingest_rss():
    stored = []
    linkedin_count = 0
    total_entries = 0

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
            total_entries += 1

            title = entry.get("title", "")
            summary = clean_html(entry.get("summary", ""))

            content_list = entry.get("content", [])
            content = clean_html(
                content_list[0].get("value", "") if content_list else ""
            )

            full_text = f"{title}\n\n{summary}\n\n{content}".strip()

            if len(full_text) < 100:
                continue

            tags = get_domain_tags(full_text)

            # Safe publish date
            try:
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    pub_dt = datetime(
                        *entry.published_parsed[:6]
                    ).isoformat()
                else:
                    pub_dt = entry.get("published", "")
            except Exception:
                pub_dt = entry.get("published", "")

            link = entry.get("link", "")

            # Deterministic platform tagging via feed name
            is_linkedin = name.startswith("google_linkedin")

            if is_linkedin:
                linkedin_count += 1
            # ─────────────────────────────
            # LinkedIn GTM Signal Layer
            # ─────────────────────────────
            if is_linkedin:
                text_l = full_text.lower()

                if any(k in text_l for k in ["daily money manager", "dmm", "care manager"]):
                    tags.append("practitioner_signal")

                if any(k in text_l for k in ["scam", "fraud", "financial exploitation"]):
                    tags.append("vulnerability_event")

                if any(k in text_l for k in ["policy", "medicaid", "guardianship"]):
                    tags.append("regulatory_discussion")

                if any(k in text_l for k in ["bill pay", "financial oversight", "coordination"]):
                    tags.append("product_relevance")

                if any(k in text_l for k in ["opinion", "insight", "thoughts on"]):
                    tags.append("influence_channels")
                    
            meta = {
                "source": "rss",
                "platform": "linkedin" if is_linkedin else "rss",
                "feed_name": name,
                "feed_url": url,
                "title": title,
                "url": link,
                "published": pub_dt,
                "domain_tags": tags,
            }

            chunks = chunk_text(full_text)

            for chunk in chunks:
                cid = save_chunk(chunk, meta)
                stored.append(cid)

            print(f"  ✓ {title[:70]}")
            print(f"    tags: {tags} | {len(chunks)} chunk(s)")

    print(f"\nLinkedIn entries this run: {linkedin_count}")
    print(f"Total entries processed: {total_entries}")
    print(f"── RSS done: {len(stored)} chunks ──")

    return stored


if __name__ == "__main__":
    ingest_rss()
