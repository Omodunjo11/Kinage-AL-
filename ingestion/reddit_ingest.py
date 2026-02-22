"""
AL Ingestion — Reddit Pipeline
Pulls posts from caregiving/aging subreddits, strips PII, tags by taxonomy domain.

Run from ~/AL:
    python3 ingestion/reddit_ingest.py

Requirements: pip install praw pyyaml openai
Reddit credentials: https://www.reddit.com/prefs/apps → create app (script type)
"""

import os
import re
import json
import yaml
import hashlib
import praw
from datetime import datetime

# ── Load config ───────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(BASE, "config/config.yaml")) as f:
    config = yaml.safe_load(f)

with open(os.path.join(BASE, config["taxonomy"]["path"].lstrip("./"))) as f:
    taxonomy = yaml.safe_load(f)

reddit_cfg = config["ingestion"]["reddit"]
api = config["api_keys"]

# ── Build trigger list from taxonomy ─────────────────────────────────
def get_triggers() -> list[str]:
    out = []
    for domain in taxonomy["domains"].values():
        for sub in domain.get("subdomain", {}).values():
            out.extend(sub.get("triggers", []))
    return [t.lower() for t in out]

TRIGGERS = get_triggers()

def get_domain_tags(text: str) -> list[str]:
    text_l = text.lower()
    tags = []
    for name, domain in taxonomy["domains"].items():
        for sub in domain.get("subdomain", {}).values():
            if any(t.lower() in text_l for t in sub.get("triggers", [])):
                if name not in tags:
                    tags.append(name)
    return tags

def is_relevant(text: str) -> bool:
    text_l = text.lower()
    return any(t in text_l for t in TRIGGERS)

def strip_pii(text: str) -> str:
    text = re.sub(r'\S+@\S+\.\S+', '[email]', text)
    text = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '[phone]', text)
    text = re.sub(r'\$\d{3,}(?:,\d{3})*(?:\.\d{2})?', '[amount]', text)
    # Remove names preceded by "My mom" / "My dad" patterns — keep the signal not the story
    text = re.sub(r"\bmy (mom|dad|mother|father|parent)(?:'s)? name is \w+", 
                  r'my \1', text, flags=re.IGNORECASE)
    return text

def chunk_text(text: str, size: int = 400, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks, step = [], size - overlap
    for i in range(0, len(words), step):
        c = " ".join(words[i:i + size])
        if len(c.strip()) > 60:
            chunks.append(c)
    return chunks

def save_chunk(chunk: str, metadata: dict) -> str:
    out_dir = os.path.join(BASE, "corpus/external/reddit")
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

# ── Reddit client ─────────────────────────────────────────────────────
reddit = praw.Reddit(
    client_id=api["reddit_client_id"],
    client_secret=api["reddit_client_secret"],
    user_agent=api["reddit_user_agent"],
)

# ── Main ──────────────────────────────────────────────────────────────
def ingest_reddit():
    stored = []

    for sub_name in reddit_cfg["subreddits"]:
        print(f"\n── r/{sub_name} ──")
        subreddit = reddit.subreddit(sub_name)

        for post in subreddit.top(
            time_filter=reddit_cfg["time_filter"],
            limit=reddit_cfg["posts_per_subreddit"]
        ):
            if post.score < reddit_cfg["min_score"]:
                continue

            raw = f"{post.title}\n\n{post.selftext or ''}".strip()

            if not is_relevant(raw):
                continue

            clean = strip_pii(raw)
            tags = get_domain_tags(clean)

            meta = {
                "source": "reddit",
                "subreddit": sub_name,
                "post_id": post.id,
                "url": f"https://reddit.com{post.permalink}",
                "score": post.score,
                "num_comments": post.num_comments,
                "created_utc": datetime.utcfromtimestamp(post.created_utc).isoformat(),
                "domain_tags": tags,
                # username NOT stored — PII policy
            }

            for chunk in chunk_text(clean):
                cid = save_chunk(chunk, meta)
                stored.append(cid)

            print(f"  ✓ [{post.score}] {post.title[:65]}...")
            print(f"    tags: {tags}")

    print(f"\n── Reddit done: {len(stored)} chunks ──")
    return stored


if __name__ == "__main__":
    ingest_reddit()
