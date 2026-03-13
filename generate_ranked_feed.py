# generate_ranked_feed.py

import json
import os
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

def score_chunks(chunks: List[Dict]) -> List[Dict]:
    scored = []
    intersection_count = 0

    for chunk in chunks:
        text = chunk.get("text", "")

        if not text.strip():
            chunk["score"] = 0.0
            scored.append(chunk)
            continue

        try:
            total_score, domain_scores = compute_total_signal(text)
            
            # Convert numpy type to plain Python float
            chunk["score"] = float(total_score)
            
            # Convert domain scores dict → clean string array, filter weak signals
            if "metadata" not in chunk:
                chunk["metadata"] = {}
            
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
