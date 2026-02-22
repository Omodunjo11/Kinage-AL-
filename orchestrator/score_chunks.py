"""
AL Orchestrator — Score Chunks
Calculates relevance scores for chunks based on taxonomy domain tags.

Scoring logic:
- Base score = sum of domain weights
- Intersection multiplier (1.5x) applied if tags match priority_intersections
- Time decay factor applied based on publication date
- Final score = base_score * intersection_multiplier * time_decay_factor
- Updates chunk metadata with 'score' field

Run from ~/AL:
    python3 orchestrator/score_chunks.py
"""

import os
import json
import yaml
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).parent.parent

# Load config and taxonomy
with open(BASE / "config" / "config.yaml") as f:
    config = yaml.safe_load(f)

with open(BASE / config["taxonomy"]["path"].lstrip("./")) as f:
    taxonomy = yaml.safe_load(f)

intersection_multiplier = taxonomy.get("intersection_multiplier", 1.5)
priority_intersections = taxonomy.get("priority_intersections", [])

# Time decay configuration
TIME_DECAY_HALF_LIFE_DAYS = 30  # Days for decay factor to reach 0.5

# Build domain weights lookup
domain_weights = {}
for name, domain in taxonomy["domains"].items():
    domain_weights[name] = domain.get("weight", 0.0)


def compute_decay(metadata: dict) -> float:
    """Calculate time decay factor based on publication date from metadata.
    
    Uses hyperbolic decay: decay = 1 / (1 + (days_old / 30))
    - At 0 days: decay = 1.0 (no decay)
    - At 30 days: decay = 0.5 (50% of original)
    - At 60 days: decay = 0.33 (33% of original)
    - Approaches 0 as days_old increases
    """
    published = metadata.get("published") or metadata.get("published_at")
    if not published:
        return 1.0
    
    try:
        dt = datetime.fromisoformat(published)
        now = datetime.now(timezone.utc)
        days_old = (now - dt).days
        return 1 / (1 + (days_old / TIME_DECAY_HALF_LIFE_DAYS))
    except:
        return 1.0


def calculate_score(tags: list[str], metadata: dict = None) -> float:
    """Calculate score for a chunk based on its domain tags and metadata.
    
    Args:
        tags: List of domain tags
        metadata: Chunk metadata dict (for computing decay)
    
    Returns:
        Final score = base_score * intersection_multiplier * decay
    """
    if not tags:
        return 0.0
    
    # Base score: sum of domain weights
    base_score = sum(domain_weights.get(tag, 0.0) for tag in tags)
    
    # Check for priority intersections
    tags_set = set(tags)
    tags_match_priority_intersection = False
    
    for intersection in priority_intersections:
        intersection_set = set(intersection)
        if intersection_set.issubset(tags_set):
            tags_match_priority_intersection = True
            break
    
    # Apply intersection multiplier if applicable
    if tags_match_priority_intersection:
        base_score *= intersection_multiplier
    
    # Compute decay from metadata
    metadata = metadata or {}
    decay = compute_decay(metadata)
    
    # Final score
    final_score = base_score * decay
    
    return round(final_score, 4)


def score_chunks_in_directory(directory: Path):
    """Score all chunks in a directory."""
    if not directory.exists():
        print(f"⚠ Directory not found: {directory}")
        return
    
    scored = 0
    skipped = 0
    
    for json_file in directory.glob("*.json"):
        try:
            with open(json_file) as f:
                chunk = json.load(f)
            
            metadata = chunk.get("metadata", {})
            tags = metadata.get("domain_tags", [])
            
            # Calculate base score and check for intersections
            base_score = sum(domain_weights.get(tag, 0.0) for tag in tags) if tags else 0.0
            
            tags_set = set(tags)
            tags_match_priority_intersection = False
            for intersection in priority_intersections:
                intersection_set = set(intersection)
                if intersection_set.issubset(tags_set):
                    tags_match_priority_intersection = True
                    break
            
            if tags_match_priority_intersection:
                base_score *= intersection_multiplier
            
            # Compute decay
            decay = compute_decay(metadata)
            
            # Final score
            final_score = base_score * decay
            
            # Update chunk with score and decay
            if "metadata" not in chunk:
                chunk["metadata"] = {}
            chunk["metadata"]["score"] = round(final_score, 4)
            chunk["metadata"]["decay"] = round(decay, 4)
            
            # Write back
            with open(json_file, "w") as f:
                json.dump(chunk, f, indent=2)
            
            scored += 1
            
        except Exception as e:
            print(f"⚠ Error processing {json_file.name}: {e}")
            skipped += 1
    
    return scored, skipped


def main():
    """Score chunks across all corpus directories."""
    print("── Scoring Chunks ──\n")
    
    # Score external sources
    external_dirs = [
        BASE / "corpus" / "external" / "rss",
        BASE / "corpus" / "external" / "web",
        BASE / "corpus" / "external" / "reddit",
    ]
    
    total_scored = 0
    total_skipped = 0
    
    for dir_path in external_dirs:
        if dir_path.exists():
            print(f"📁 {dir_path.relative_to(BASE)}")
            scored, skipped = score_chunks_in_directory(dir_path)
            total_scored += scored
            total_skipped += skipped
            print(f"   ✓ Scored: {scored} | ⚠ Skipped: {skipped}\n")
    
    # Score internal corpus if exists
    internal_dir = BASE / "corpus" / "internal"
    if internal_dir.exists():
        print(f"📁 {internal_dir.relative_to(BASE)}")
        scored, skipped = score_chunks_in_directory(internal_dir)
        total_scored += scored
        total_skipped += skipped
        print(f"   ✓ Scored: {scored} | ⚠ Skipped: {skipped}\n")
    
    print(f"── Done: {total_scored} chunks scored, {total_skipped} skipped ──")


if __name__ == "__main__":
    main()
