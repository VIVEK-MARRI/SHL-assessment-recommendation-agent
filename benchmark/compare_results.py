import json

with open('benchmark/pipeline_baseline.json') as f:
    baseline = json.load(f)
with open('benchmark/pipeline_improved.json') as f:
    improved = json.load(f)

bs = baseline.get('summary', {})
is_ = improved.get('summary', {})

KEY_MAP = {
    'num_queries': 'num_queries',
    'precision@1': 'precision@1',
    'precision@3': 'precision@3',
    'precision@5': 'precision@5',
    'precision@10': 'precision@10',
    'recall@10': 'recall@10',
    'mrr': 'mrr',
    'ndcg@10': 'ndcg@10',
    'avg_latency_ms': 'avg_latency_ms',
    'coverage_pct': 'coverage_pct',
}

print('=== OVERALL ===')
print('%-22s %12s %12s %12s' % ('Metric', 'Baseline', 'Improved', 'Delta'))
print('-' * 60)
for label, key in KEY_MAP.items():
    bv = bs.get(key, 'N/A')
    iv = is_.get(key, 'N/A')
    delta = ''
    if isinstance(bv, (int,float)) and isinstance(iv, (int,float)):
        d = iv - bv
        if isinstance(d, float):
            delta = '%+.4f' % d
        else:
            delta = '%+d' % d
    print('%-22s %12s %12s %12s' % (label, str(bv)[:12], str(iv)[:12], delta))

print()
print('=== BY CATEGORY (recall@10) ===')
cats = sorted(set(list(baseline.get('cat_summary',{}).keys()) + list(improved.get('cat_summary',{}).keys())))
print('%-25s %10s %10s %10s' % ('Category', 'Base R@10', 'Imp R@10', 'Delta'))
print('-' * 60)
for cat in cats:
    bcat = baseline.get('cat_summary',{}).get(cat, {})
    icat = improved.get('cat_summary',{}).get(cat, {})
    b_r = bcat.get('recall@10', 'N/A')
    i_r = icat.get('recall@10', 'N/A')
    delta = ''
    if isinstance(b_r, (int,float)) and isinstance(i_r, (int,float)):
        d = i_r - b_r
        delta = '%+.4f' % d
    b_str = '%.4f' % b_r if isinstance(b_r, float) else str(b_r)
    i_str = '%.4f' % i_r if isinstance(i_r, float) else str(i_r)
    print('%-25s %10s %10s %10s' % (cat, b_str, i_str, delta))

print()
print('=== BY CATEGORY (precision@1) ===')
print('%-25s %10s %10s %10s' % ('Category', 'Base P@1', 'Imp P@1', 'Delta'))
print('-' * 60)
for cat in cats:
    bcat = baseline.get('cat_summary',{}).get(cat, {})
    icat = improved.get('cat_summary',{}).get(cat, {})
    b_p = bcat.get('precision@1', 'N/A')
    i_p = icat.get('precision@1', 'N/A')
    delta = ''
    if isinstance(b_p, (int,float)) and isinstance(i_p, (int,float)):
        d = i_p - b_p
        delta = '%+.4f' % d
    b_str = '%.4f' % b_p if isinstance(b_p, float) else str(b_p)
    i_str = '%.4f' % i_p if isinstance(i_p, float) else str(i_p)
    print('%-25s %10s %10s %10s' % (cat, b_str, i_str, delta))
