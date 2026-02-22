"""
AL Master Ingestion Runner
Runs all enabled pipelines. Run every Monday 6am via cron.

Run from ~/AL:
    python3 ingestion/run_all.py

Cron setup (add via `crontab -e`):
    0 6 * * 1 cd ~/AL && source venv/bin/activate && python3 ingestion/run_all.py >> outputs/ingestion.log 2>&1
"""

import sys
import os
import yaml
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

with open(os.path.join(BASE, "config/config.yaml")) as f:
    config = yaml.safe_load(f)

cfg = config["ingestion"]

print(f"\n{'='*60}")
print(f"AL INGESTION — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"{'='*60}\n")

results = {}

# ── Reddit ────────────────────────────────────────────────────────────
if cfg.get("reddit", {}).get("enabled"):
    print("▶ Reddit")
    from ingestion.reddit_ingest import ingest_reddit
    results["reddit"] = ingest_reddit()
else:
    print("— Reddit disabled")

# ── RSS ───────────────────────────────────────────────────────────────
if cfg.get("rss", {}).get("enabled"):
    print("\n▶ RSS Feeds")
    from ingestion.rss_ingest import ingest_rss
    results["rss"] = ingest_rss()
else:
    print("— RSS disabled")

# ── Web ───────────────────────────────────────────────────────────────
if cfg.get("web", {}).get("enabled"):
    print("\n▶ Competitor Web")
    from ingestion.web_ingest import ingest_web
    results["web"] = ingest_web()
else:
    print("— Web scraping disabled")

# ── LinkedIn manual ───────────────────────────────────────────────────
li = cfg.get("linkedin", {})
if li.get("enabled"):
    print("\n▶ LinkedIn (manual files)")
    manual_dir = os.path.join(BASE, li["manual_input_dir"].lstrip("./"))
    if os.path.exists(manual_dir):
        files = [f for f in os.listdir(manual_dir) if f.endswith(".txt")]
        print(f"  {len(files)} .txt file(s) found in {manual_dir}")
        # Simple pass-through: copy text as chunks tagged as linkedin source
        import json, hashlib
        stored = []
        for fname in files:
            with open(os.path.join(manual_dir, fname)) as f:
                text = f.read().strip()
            if not text:
                continue
            out_dir = os.path.join(BASE, "corpus/external/linkedin")
            os.makedirs(out_dir, exist_ok=True)
            cid = hashlib.md5(text.encode()).hexdigest()[:12]
            record = {
                "id": cid,
                "text": text[:4000],
                "metadata": {"source": "linkedin_manual", "filename": fname},
                "ingested_at": datetime.utcnow().isoformat(),
            }
            with open(os.path.join(out_dir, f"{cid}.json"), "w") as out:
                json.dump(record, out, indent=2)
            stored.append(cid)
            print(f"  ✓ {fname}")
        results["linkedin"] = stored
    else:
        print(f"  ⚠ manual_input_dir not found: {manual_dir}")
else:
    print("— LinkedIn disabled (manual mode: drop .txt files into corpus/linkedin_manual/)")

# ── Summary ───────────────────────────────────────────────────────────
total = sum(len(v) for v in results.values())
print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")
for src, chunks in results.items():
    print(f"  {src:15} {len(chunks):4} chunks")
print(f"  {'TOTAL':15} {total:4} chunks")
print(f"{'='*60}")
print("\nNext: python3 orchestrator/generate_brief.py")
