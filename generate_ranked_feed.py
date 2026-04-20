# generate_ranked_feed.py

import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict

# ✅ Correct scorer for Kinage AL
from utils.semantic_domain_scorer import compute_total_signal


CORPUS_DIRS = [
    "corpus/external/rss",
    "corpus/external/web",
]

OUTPUT_PATH = "outputs/ranked_chunks.json"
SCORE_THRESHOLD = 0.0  # raise to 0.1+ if you want to filter noise

# Recency decay: half-life of 14 days — items 2 weeks old get ~50% score boost
RECENCY_HALF_LIFE_DAYS = 14


# ──────────────────────────────────────────────────────────────
# Load
# ──────────────────────────────────────────────────────────────

def load_all_chunks() -> List[Dict]:
    chunks = []

    for dir_path in CORPUS_DIRS:
        path = Path(dir_path)
        if not path.exists():
            continue

        for file in path.rglob("*.json"):
            try:
                with open(file, "r") as f:
                    data = json.load(f)

                if isinstance(data, list):
                    chunks.extend(data)
                elif isinstance(data, dict):
                    chunks.append(data)

            except Exception as e:
                print(f"⚠️  Skipping {file}: {e}")

    return chunks


# ──────────────────────────────────────────────────────────────
# Score
# ──────────────────────────────────────────────────────────────

def parse_date(value: str) -> datetime | None:
    if not value:
        return None
    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(value.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def age_bucket(days: float) -> str:
    if days <= 1:
        return "today"
    if days <= 7:
        return "this_week"
    if days <= 30:
        return "this_month"
    return "older"


def recency_multiplier(days: float) -> float:
    return math.exp(-days / RECENCY_HALF_LIFE_DAYS)


def score_chunks(chunks: List[Dict]) -> List[Dict]:
    scored = []
    intersection_count = 0

    now = datetime.now(timezone.utc)

    for chunk in chunks:
        text = chunk.get("text", "")

        if not text.strip():
            chunk["score"] = 0.0
            chunk["age_bucket"] = "older"
            scored.append(chunk)
            continue

        # ── Recency ──────────────────────────────────────
        if "metadata" not in chunk:
            chunk["metadata"] = {}

        pub_str = chunk["metadata"].get("published") or chunk.get("ingested_at", "")
        pub_dt = parse_date(pub_str)
        days_old = (now - pub_dt).total_seconds() / 86400 if pub_dt else 999
        chunk["age_bucket"] = age_bucket(days_old)
        decay = recency_multiplier(days_old)

        try:
            total_score, domain_scores = compute_total_signal(text)

            # Apply recency decay to raw signal score
            chunk["score"] = float(total_score) * decay

            if isinstance(domain_scores, dict):
                chunk["metadata"]["domain_tags"] = [
                    str(k) for k, v in domain_scores.items() if float(v) > 0.35
                ]
            elif isinstance(domain_scores, (list, tuple)):
                chunk["metadata"]["domain_tags"] = [str(t) for t in domain_scores]
            else:
                chunk["metadata"]["domain_tags"] = []

            if chunk["score"] > 0:
                intersection_count += 1

        except Exception as e:
            print(f"⚠️  Scoring failed for {chunk.get('id', 'unknown')}: {e}")
            chunk["score"] = 0.0

        scored.append(chunk)

    print(f"\nChunks with non-zero score: {intersection_count}")
    return scored


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────

def generate_ranked_feed():
    print("\n📂 Loading chunks...")
    chunks = load_all_chunks()
    print(f"Total chunks: {len(chunks)}")

    print("\n⚙️  Scoring chunks...")
    chunks = score_chunks(chunks)

    print("\n📊 Sorting by score...")
    chunks.sort(key=lambda c: c.get("score", 0.0), reverse=True)

    if SCORE_THRESHOLD > 0:
        before = len(chunks)
        chunks = [
            c for c in chunks
            if c.get("score", 0.0) >= SCORE_THRESHOLD
        ]
        print(f"Filtered {before - len(chunks)} below threshold {SCORE_THRESHOLD}")

    scores = [c.get("score", 0.0) for c in chunks]

    if scores:
        print(f"\nScore range: {min(scores):.4f} - {max(scores):.4f}")
        print(f"High signals (≥0.65): {sum(1 for s in scores if s >= 0.65)}")
        print(f"Critical signals (≥0.80): {sum(1 for s in scores if s >= 0.80)}")

    os.makedirs("outputs", exist_ok=True)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(chunks, f, indent=2, default=str)

    print(f"\n✅ Written {len(chunks)} chunks → {OUTPUT_PATH}")


if __name__ == "__main__":
    generate_ranked_feed()
