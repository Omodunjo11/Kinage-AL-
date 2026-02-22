"""
AL Ingestion — Competitor Web Scraper
Targets: SilverBills, EverSafe, myFloc, Carefull, True Link Financial
Respects robots.txt. Polite crawl delay (1.5s between requests).

Run from ~/AL:
    python3 ingestion/web_ingest.py

Requirements: pip install requests beautifulsoup4 lxml pyyaml
"""

import os
import re
import json
import yaml
import time
import hashlib
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(BASE, "config/config.yaml")) as f:
    config = yaml.safe_load(f)

with open(os.path.join(BASE, config["taxonomy"]["path"].lstrip("./"))) as f:
    taxonomy = yaml.safe_load(f)

web_cfg = config["ingestion"]["web"]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AL_KinageIntelligence/1.0; research)"}

def get_domain_tags(text: str) -> list[str]:
    text_l = text.lower()
    tags = []
    for name, domain in taxonomy["domains"].items():
        for sub in domain.get("subdomain", {}).values():
            if any(t.lower() in text_l for t in sub.get("triggers", [])):
                if name not in tags:
                    tags.append(name)
    return tags

def can_fetch(url: str) -> bool:
    if not web_cfg.get("respect_robots_txt", True):
        return True
    try:
        p = urlparse(url)
        rp = RobotFileParser()
        rp.set_url(f"{p.scheme}://{p.netloc}/robots.txt")
        rp.read()
        return rp.can_fetch(HEADERS["User-Agent"], url)
    except Exception:
        return True

def get_post_links(base_url: str, html: str, max_links: int = 15) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    base_parsed = urlparse(base_url)
    links = set()
    for a in soup.find_all("a", href=True):
        full = urljoin(base_url, a["href"])
        p = urlparse(full)
        if p.netloc != base_parsed.netloc:
            continue
        if any(full.endswith(ext) for ext in [".pdf", ".jpg", ".png", ".xml", ".rss"]):
            continue
        if "#" in full:
            continue
        if len(p.path.strip("/").split("/")) < 2:
            continue
        links.add(full)
        if len(links) >= max_links:
            break
    return list(links)

def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()
    body = (
        soup.find("article")
        or soup.find("main")
        or soup.find(class_=lambda c: c and any(
            x in str(c).lower() for x in ["post", "article", "content", "entry"]
        ))
        or soup.find("body")
    )
    text = (body or soup).get_text(separator=" ", strip=True)
    return re.sub(r'\s+', ' ', text).strip()

def chunk_text(text: str, size: int = 400, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks, step = [], size - overlap
    for i in range(0, len(words), step):
        c = " ".join(words[i:i + size])
        if len(c.strip()) > 80:
            chunks.append(c)
    return chunks

def save_chunk(chunk: str, metadata: dict) -> str:
    out_dir = os.path.join(BASE, "corpus/external/web")
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

def ingest_web():
    stored = []
    max_pages = web_cfg.get("max_pages_per_site", 10)

    for site in web_cfg["competitors"]:
        name = site["name"]
        base_url = site["url"]
        print(f"\n── {name} ({base_url}) ──")

        if not can_fetch(base_url):
            print(f"  ⛔ robots.txt blocks {base_url} — skipping")
            continue

        try:
            resp = requests.get(base_url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"  ⚠ Cannot fetch index: {e}")
            continue

        links = get_post_links(base_url, resp.text, max_links=max_pages)
        print(f"  {len(links)} post links found")

        for url in links:
            if not can_fetch(url):
                continue
            try:
                time.sleep(1.5)
                post_resp = requests.get(url, headers=HEADERS, timeout=10)
                post_resp.raise_for_status()
            except Exception as e:
                print(f"  ⚠ Skip {url}: {e}")
                continue

            text = extract_text(post_resp.text)
            if len(text) < 200:
                continue

            tags = get_domain_tags(text)
            soup = BeautifulSoup(post_resp.text, "html.parser")
            title_tag = soup.find("title")
            title = title_tag.get_text().strip() if title_tag else url

            meta = {
                "source": "web",
                "competitor": name,
                "base_url": base_url,
                "url": url,
                "title": title[:200],
                "domain_tags": tags,
            }

            chunks = chunk_text(text)
            for chunk in chunks:
                cid = save_chunk(chunk, meta)
                stored.append(cid)

            print(f"  ✓ {title[:65]}")
            print(f"    tags: {tags} | {len(chunks)} chunk(s)")

    print(f"\n── Web done: {len(stored)} chunks ──")
    return stored


if __name__ == "__main__":
    ingest_web()
