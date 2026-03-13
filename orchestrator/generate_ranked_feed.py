"""
AL Orchestrator — Generate Ranked Feed
Generates a ranked feed of chunks sorted by semantic relevance score.

Run:
    python3 -m orchestrator.generate_ranked_feed
    python3 -m orchestrator.generate_ranked_feed --limit 50
    python3 -m orchestrator.generate_ranked_feed --min-score 0.1
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
from typing import List, Dict

from utils.semantic_domain_scorer import compute_total_signal

BASE = Path(__file__).parent.parent


# ─────────────────────────────────────────────
# Scoring
# ─────────────────────────────────────────────

def score_chunk(chunk: Dict) -> Dict:
    text = chunk.get("text", "")

    if not text.strip():
        chunk["score"] = 0.0
        return chunk

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

    except Exception as e:
        print(f"⚠ Scoring failed: {e}")
        chunk["score"] = 0.0

    return chunk


def get_chunk_score(chunk: Dict) -> float:
    return float(chunk.get("score", 0.0))


# ─────────────────────────────────────────────
# Loading
# ─────────────────────────────────────────────

def load_all_chunks(directories: List[Path]) -> List[Dict]:
    chunks = []

    for directory in directories:
        if not directory.exists():
            continue

        for json_file in directory.glob("*.json"):
            try:
                with open(json_file) as f:
                    chunk = json.load(f)

                chunk["_source_file"] = str(json_file.relative_to(BASE))

                # Preserve pre-computed intelligence fields from score_chunks.py
                # These are written by orchestrator/score_chunks.py for chunks >= 0.65
                intelligence = {
                    "summary":        chunk.get("summary"),
                    "why_it_matters": chunk.get("why_it_matters"),
                    "risk_type":      chunk.get("risk_type"),
                    "entities":       chunk.get("entities"),
                    "severity":       chunk.get("severity"),
                }

                chunk = score_chunk(chunk)

                # Re-attach intelligence fields after scoring (score_chunk doesn't touch them)
                for key, val in intelligence.items():
                    if val is not None and val != "" and val != []:
                        chunk["metadata"][key] = val

                chunks.append(chunk)

            except Exception as e:
                print(f"⚠ Error loading {json_file.name}: {e}")

    return chunks


# ─────────────────────────────────────────────
# Statistics
# ─────────────────────────────────────────────

def generate_stats(chunks: List[Dict]) -> Dict:
    stats = {
        "total": len(chunks),
        "by_source": defaultdict(int),
        "by_tag": defaultdict(int),
        "score_range": {"min": float("inf"), "max": float("-inf")},
        "intersections": 0,
    }

    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        source = metadata.get("source", "unknown")
        tags = metadata.get("domain_tags", [])
        score = get_chunk_score(chunk)

        stats["by_source"][source] += 1

        for tag in tags:
            stats["by_tag"][tag] += 1

        if len(tags) > 1:
            stats["intersections"] += 1

        stats["score_range"]["min"] = min(stats["score_range"]["min"], score)
        stats["score_range"]["max"] = max(stats["score_range"]["max"], score)

    if stats["score_range"]["min"] == float("inf"):
        stats["score_range"]["min"] = 0.0
    if stats["score_range"]["max"] == float("-inf"):
        stats["score_range"]["max"] = 0.0

    return stats


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate ranked feed of chunks")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--min-score", type=float, default=0.0)
    parser.add_argument("--write-json", type=str, default=None)
    parser.add_argument("--stats-only", action="store_true")

    args = parser.parse_args()

    directories = [
        BASE / "corpus" / "external" / "rss",
        BASE / "corpus" / "external" / "web",
        BASE / "corpus" / "external" / "reddit",
        BASE / "corpus" / "internal",
    ]

    print("── Loading + Scoring Chunks ──")
    chunks = load_all_chunks(directories)

    # Apply min-score filter AFTER scoring
    if args.min_score:
        chunks = [c for c in chunks if get_chunk_score(c) >= args.min_score]

    print(f"Loaded {len(chunks)} scored chunks\n")

    chunks.sort(key=get_chunk_score, reverse=True)

    if args.limit:
        chunks = chunks[:args.limit]

    stats = generate_stats(chunks)

    print("\n── Statistics ──\n")
    print(f"Total chunks: {stats['total']}")
    print(f"Score range: {stats['score_range']['min']:.4f} - {stats['score_range']['max']:.4f}")
    print(f"Chunks with intersections: {stats['intersections']}\n")

    print("By source:")
    for source, count in sorted(stats["by_source"].items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count}")

    print("\nBy tag:")
    for tag, count in sorted(stats["by_tag"].items(), key=lambda x: x[1], reverse=True):
        print(f"  {tag}: {count}")

    if args.write_json:
        out_list = [{k: v for k, v in c.items() if not k.startswith("_")} for c in chunks]
        out_path = Path(args.write_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        with open(out_path, "w") as f:
            json.dump(out_list, f, indent=2, default=str)



        print(f"\n✓ Ranked JSON written to {args.write_json} ({len(out_list)} chunks)")


if __name__ == "__main__":
    main()
