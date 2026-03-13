#!/bin/bash

set -e

echo "⚙️  Step 1 — Scoring chunks + generating AI summaries..."
python3 -m orchestrator.score_chunks

echo ""
echo "📊 Step 2 — Building ranked feed..."
python3 -m orchestrator.generate_ranked_feed --write-json outputs/ranked_chunks.json

echo ""
echo "📦 Step 3 — Copying to kinage-app..."
cp outputs/ranked_chunks.json ../kinage-app/data/ranked_chunks.json

echo ""
echo "🚀 Step 4 — Pushing to GitHub..."
cd ../kinage-app

git add data/ranked_chunks.json

if git diff --cached --quiet; then
  echo "ℹ️  No changes detected. Nothing to commit."
else
  git commit -m "signals refresh $(date '+%Y-%m-%d %H:%M')"
  git push
  echo "✅ Pushed. Vercel will deploy automatically."
fi
