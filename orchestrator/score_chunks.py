"""
AL Orchestrator — Score Chunks

Final score formula:
    (Base Domain Weight + Intersection Multiplier) 
    × Time Decay 
    × Authority Weight
"""

import json
import yaml
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).parent.parent

# -------------------------
# Load Config + Taxonomy
# -------------------------

with open(BASE / "config" / "config.yaml") as f:
    config = yaml.safe_load(f)

with open(BASE / config["taxonomy"]["path"].lstrip("./")) as f:
    taxonomy = yaml.safe_load(f)

intersection_multiplier = taxonomy.get("intersection_multiplier", 1.5)
priority_intersections = taxonomy.get("priority_intersections", [])

domain_weights = {
    name: domain.get("weight", 0.0)
    for name, domain in taxonomy["domains"].items()
}

TIME_DECAY_HALF_LIFE_DAYS = 30

SOURCE_WEIGHTS = {
    "rss": 0.8,
    "web": 0.6,
    "reddit": 0.5,
    "federal_register": 1.3,
    "ftc_enforcement": 1.4,
    "ftc_newsroom": 1.2,
    "linkedin_manual": 1.15,
}


# -------------------------
# Scoring Components
# -------------------------

def compute_decay(metadata: dict) -> float:
    published = metadata.get("published") or metadata.get("published_at")
    if not published:
        return 1.0

    try:
        dt = datetime.fromisoformat(published)
        now = datetime.now(timezone.utc)
        days_old = (now - dt).days
        return 1 / (1 + (days_old / TIME_DECAY_HALF_LIFE_DAYS))
    except Exception:
        return 1.0


def get_authority_weight(metadata: dict) -> float:
    source = metadata.get("source_type") or metadata.get("source")
    return SOURCE_WEIGHTS.get(source, 1.0)


def calculate_score(tags: list[str], metadata: dict) -> float:
    if not tags:
        return 0.0

    base_score = sum(domain_weights.get(tag, 0.0) for tag in tags)

    tags_set = set(tags)
    for intersection in priority_intersections:
        if set(intersection).issubset(tags_set):
            base_score *= intersection_multiplier
            break

    decay = compute_decay(metadata)
    authority = get_authority_weight(metadata)

    final_score = base_score * decay * authority
    return round(final_score, 4)


# -------------------------
# Directory Scoring
# -------------------------

def score_chunks_in_directory(directory: Path):
    if not directory.exists():
        print(f"⚠ Directory not found: {directory}")
        return 0, 0

    scored = 0
    skipped = 0

    for json_file in directory.glob("*.json"):
        try:
            with open(json_file) as f:
                chunk = json.load(f)

            metadata = chunk.get("metadata", {})
            tags = metadata.get("domain_tags", [])

            new_score = calculate_score(tags, metadata)

            # Remove any old metadata score to prevent confusion
            if "score" in metadata:
                del metadata["score"]

            chunk["score"] = new_score

            with open(json_file, "w") as f:
                json.dump(chunk, f, indent=2)

            scored += 1

        except Exception:
            skipped += 1

    return scored, skipped


# -------------------------
# Main Runner
# -------------------------

def main():
    print("── Scoring Chunks ──\n")

    directories = [
        BASE / "corpus" / "external" / "rss",
        BASE / "corpus" / "external" / "web",
        BASE / "corpus" / "external" / "reddit",
        BASE / "corpus" / "internal",
    ]

    total_scored = 0
    total_skipped = 0

    for directory in directories:
        if directory.exists():
            print(f"📁 {directory.relative_to(BASE)}")
            scored, skipped = score_chunks_in_directory(directory)
            total_scored += scored
            total_skipped += skipped
            print(f"   ✓ Scored: {scored} | ⚠ Skipped: {skipped}\n")

    print(f"── Done: {total_scored} scored, {total_skipped} skipped ──")


if __name__ == "__main__":
    main()
