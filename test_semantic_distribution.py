import os
import json
from utils.semantic_domain_scorer import compute_total_signal

results = []

for file in os.listdir("corpus/external/rss"):
    path = os.path.join("corpus/external/rss", file)

    with open(path) as f:
        article = json.load(f)

    score, breakdown = compute_total_signal(article.get("text", ""))
    results.append((file, score, article["metadata"]["title"]))

print("Total Articles Processed:", len(results))

results_sorted = sorted(results, key=lambda x: x[1], reverse=True)

print("\nTop 10 Articles:")
for r in results_sorted[:10]:
    print(f"{r[1]:.3f} — {r[2]}")

if results:
    avg = sum(r[1] for r in results) / len(results)
    print("\nAverage Score:", avg)
    print("Max Score:", results_sorted[0][1])
    print("Min Score:", results_sorted[-1][1])
