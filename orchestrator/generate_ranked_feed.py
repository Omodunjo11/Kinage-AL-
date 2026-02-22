"""
AL Orchestrator — Generate Ranked Feed
Generates a ranked feed of chunks sorted by relevance score.

Outputs chunks sorted by score (descending) with metadata for review/analysis.

Run from ~/AL:
    python3 orchestrator/generate_ranked_feed.py
    python3 orchestrator/generate_ranked_feed.py --limit 50
    python3 orchestrator/generate_ranked_feed.py --min-score 0.1
"""

import os
import json
import argparse
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent.parent


def load_all_chunks(directories: list[Path], min_score: float = 0.0) -> list[dict]:
    """Load all chunks from specified directories, filtered by minimum score."""
    chunks = []
    
    for directory in directories:
        if not directory.exists():
            continue
        
        for json_file in directory.glob("*.json"):
            try:
                with open(json_file) as f:
                    chunk = json.load(f)
                
                score = chunk.get("metadata", {}).get("score", 0.0)
                if score >= min_score:
                    chunk["_source_file"] = str(json_file.relative_to(BASE))
                    chunks.append(chunk)
            
            except Exception as e:
                print(f"⚠ Error loading {json_file.name}: {e}")
    
    return chunks


def format_chunk(chunk: dict) -> str:
    """Format a chunk for display."""
    metadata = chunk.get("metadata", {})
    score = metadata.get("score", 0.0)
    tags = metadata.get("domain_tags", [])
    title = metadata.get("title", "No title")
    source = metadata.get("source", "unknown")
    url = metadata.get("url", "")
    
    text_preview = chunk.get("text", "")[:200] + "..." if len(chunk.get("text", "")) > 200 else chunk.get("text", "")
    
    lines = [
        f"Score: {score:.4f} | Tags: {tags} | Source: {source}",
        f"Title: {title}",
    ]
    
    if url:
        lines.append(f"URL: {url}")
    
    lines.append(f"Text: {text_preview}")
    lines.append("─" * 80)
    
    return "\n".join(lines)


def generate_stats(chunks: list[dict]) -> dict:
    """Generate statistics about the chunks."""
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
        score = metadata.get("score", 0.0)
        
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


def main():
    parser = argparse.ArgumentParser(description="Generate ranked feed of chunks")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of chunks in output (default: all)",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        help="Minimum score threshold (default: 0.0)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Only show statistics, not chunk details",
    )
    
    args = parser.parse_args()
    
    # Define directories to scan
    directories = [
        BASE / "corpus" / "external" / "rss",
        BASE / "corpus" / "external" / "web",
        BASE / "corpus" / "external" / "reddit",
        BASE / "corpus" / "internal",
    ]
    
    # Load chunks
    print("── Loading Chunks ──")
    chunks = load_all_chunks(directories, min_score=args.min_score)
    print(f"Loaded {len(chunks)} chunks (min score: {args.min_score})\n")
    
    # Sort by score (descending)
    chunks.sort(key=lambda x: x.get("metadata", {}).get("score", 0.0), reverse=True)
    
    # Apply limit
    if args.limit:
        chunks = chunks[:args.limit]
    
    # Generate statistics
    stats = generate_stats(chunks)
    
    # Prepare output
    output_lines = []
    
    if not args.stats_only:
        output_lines.append("── Ranked Feed ──\n")
        for i, chunk in enumerate(chunks, 1):
            output_lines.append(f"\n[{i}] {chunk['_source_file']}")
            output_lines.append(format_chunk(chunk))
    
    # Add statistics
    output_lines.append("\n\n── Statistics ──\n")
    output_lines.append(f"Total chunks: {stats['total']}")
    output_lines.append(f"Score range: {stats['score_range']['min']:.4f} - {stats['score_range']['max']:.4f}")
    output_lines.append(f"Chunks with intersections: {stats['intersections']}")
    output_lines.append("\nBy source:")
    for source, count in sorted(stats["by_source"].items(), key=lambda x: x[1], reverse=True):
        output_lines.append(f"  {source}: {count}")
    output_lines.append("\nBy tag:")
    for tag, count in sorted(stats["by_tag"].items(), key=lambda x: x[1], reverse=True):
        output_lines.append(f"  {tag}: {count}")
    
    # Output
    output_text = "\n".join(output_lines)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(output_text)
        print(f"✓ Output written to {args.output}")
    else:
        print(output_text)


if __name__ == "__main__":
    main()
