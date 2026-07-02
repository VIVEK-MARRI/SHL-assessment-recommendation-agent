"""Review baseline per-category results."""
import json

results = json.load(open("benchmark/baseline_results.json"))
print("Category Performance:")
print(f"{'Category':<20} {'#':>3} {'P@1':>6} {'P@3':>6} {'P@5':>6} {'R@10':>6} {'MRR':>6}")
print("-" * 55)
for cat, m in sorted(results["cat_summary"].items(), key=lambda x: -x[1]["precision@5"]):
    print(f"{cat:<20} {m['count']:>3} {m['precision@1']:>6.3f} {m['precision@3']:>6.3f} {m['precision@5']:>6.3f} {m['recall@10']:>6.3f} {m['mrr']:>6.3f}")

print()
print(f"Overall P@1: {results['summary']['precision@1']:.4f}")
print(f"Overall P@3: {results['summary']['precision@3']:.4f}")
print(f"Overall R@10: {results['summary']['recall@10']:.4f}")
print(f"Overall MRR: {results['summary']['mrr']:.4f}")
print(f"Overall NDCG@10: {results['summary']['ndcg@10']:.4f}")
