import json
from pathlib import Path

report = json.loads(Path("test_docs/results2/batch_report.json").read_text())
print(f"{'Doc':<35} {'Pages':>5} {'Blocks':>6} {'Time':>6} {'Score':>6}")
print("-" * 62)
for r in report:
    if "pages" in r:
        print(f"{r['file']:<35} {r['pages']:>5} {r['blocks']:>6} {r['time']:>5.2f}s {r['score']:>5.0%}")
    else:
        print(f"{r['file']:<35} FAIL")

scores = [r["score"] for r in report if "score" in r]
print(f"\nAverage score: {sum(scores)/len(scores):.0%}")
print(f"Perfect (100%): {sum(1 for s in scores if s >= 1.0)}/{len(scores)}")
print(f"Good (>=80%):   {sum(1 for s in scores if s >= 0.8)}/{len(scores)}")
print(f"Low (<70%):     {sum(1 for s in scores if s < 0.7)}/{len(scores)}")
