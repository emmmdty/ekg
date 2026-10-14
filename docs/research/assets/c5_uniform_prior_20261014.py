"""Full-train label/prior diagnostic, without model predictions or optimization."""
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from ekg.core.stage_bundle import sha256_file

ROOT = Path('runs/stages/R1/r1-v63-c5-20261013')
OUT = ROOT / 'learning_prior_audit-r2'
TRAIN = Path('runs/stages/A3/a3-v6-baselines-r10/preflight/data/MAVEN_ERE/train.jsonl')
MANIFEST = Path('data/protocols/v6/manifests/maven_ere_train.json')
ORDER = ROOT / 'frozen_null_control/cache/train/documents.jsonl'
SOURCE = Path('scripts/replay_forest_coref_control.py')
assert sha256_file(TRAIN) == '20ea01ebe71fb8c8e4f207368673cc71f29840a290698eefe15de3a24a3b6f05'
assert sha256_file(MANIFEST) == '47d19cc9a17e38259bfbb7f9206c675c7362f41252d23f414ea6cfd46015ca68'
assert sha256_file(SOURCE) == '293edadb3d97e2b97e32b6594c855504c8bf6f7d9a2aaf82e7a521844054d83c'
binding = json.loads((ROOT / 'training_structure_audit/report.json').read_text())
assert sha256_file(ORDER) in json.dumps(binding), 'frozen mention order hash not bound'
sys.path.insert(0, str(Path('scripts').resolve()))
from replay_forest_coref_control import posterior_scores  # noqa: E402

OUT.mkdir(exist_ok=False)
data = [json.loads(line) for line in TRAIN.read_text().splitlines()]
order = [json.loads(line) for line in ORDER.read_text().splitlines()]
ids = json.loads(MANIFEST.read_text())['doc_ids']
assert [r['id'] for r in data] == [r['id'] for r in order] == ids
assert len(ids) == len(set(ids)) == 2622
matrices = {}
rows, histogram = [], Counter()
for record, cache in zip(data, order, strict=True):
    gold = {m['id']: (e['id'], e['type']) for e in record['events'] for m in e['mention']}
    assert len(gold) == sum(len(e['mention']) for e in record['events'])
    assert set(gold) == set(cache['mentions']) and len(set(cache['mentions'])) == len(gold)
    assert [gold[mid][1] for mid in cache['mentions']] == cache['types']
    groups = defaultdict(list)
    for mid in cache['mentions']:
        groups[gold[mid][1]].append(gold[mid][0])
    positive = sum(len(e['mention']) * (len(e['mention']) - 1) // 2
                   for e in record['events'])
    legal, checked_positive = 0, 0
    predicted, tp = np.zeros(2), np.zeros(2)
    for labels in groups.values():
        n = len(labels)
        histogram[n] += 1
        legal += n * (n - 1) // 2
        if n not in matrices:
            parent = [[1 / (j + 1)] * (j + 1) for j in range(n)]
            c, product, _ = posterior_scores(parent, ['T'] * n)
            if n > 1:
                assert np.max(abs(c[np.tril_indices(n, -1)] - .5)) < 1e-12
            matrices[n] = c, product
        indices = np.tril_indices(n, -1)
        truth = np.array([labels[i] == labels[j] for i, j in zip(*indices, strict=True)],
                         dtype=bool)
        checked_positive += int(truth.sum())
        for arm, matrix in enumerate(matrices[n]):
            score = matrix[indices]
            predicted[arm] += score.sum()
            tp[arm] += score[truth].sum()
    assert positive == checked_positive
    losses = 1 - (2 * tp + 1) / (predicted + positive + 1)
    rows.append({'id': record['id'], 'legal_pairs': legal, 'positive_pairs': positive,
                 'mentions': len(gold), 'exact_prior_mass': float(predicted[0]),
                 'root_prior_mass': float(predicted[1]),
                 'exact_surrogate': float(losses[0]), 'root_surrogate': float(losses[1])})
legal = sum(r['legal_pairs'] for r in rows)
positive = sum(r['positive_pairs'] for r in rows)
assert sum(r['mentions'] for r in rows) == 66744 and max(histogram) == 28
assert legal == 66141
report = {'role': 'train label sparsity and constructed uniform parent prior, not effects',
          'method_admitted': False, 'neural_model_loaded': False, 'optimizer_steps': 0,
          'final_valid_accessed': False, 'documents': len(rows), 'legal_pairs': legal,
          'positive_pairs': positive, 'positive_density': positive / legal,
          'no_positive_pair_documents': sum(r['positive_pairs'] == 0 for r in rows),
          'no_legal_pair_documents': sum(r['legal_pairs'] == 0 for r in rows),
          'type_size_histogram': dict(sorted(histogram.items())),
          'uniform_exact_mass': sum(r['exact_prior_mass'] for r in rows),
          'uniform_root_mass': sum(r['root_prior_mass'] for r in rows),
          'mean_exact_surrogate': float(np.mean([r['exact_surrogate'] for r in rows])),
          'mean_root_surrogate': float(np.mean([r['root_surrogate'] for r in rows])),
          'input_sha256': {str(p): sha256_file(p) for p in [TRAIN, MANIFEST, ORDER, SOURCE]},
          'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'limitation': 'Uniform logits are constructed, not actual pretrained scores. '
          'Label sparsity/prior masses cannot show update direction, errors, achievable MUC, '
          'or power; no loss/scale/endpoint or sealed result is changed.'}
(OUT / 'documents.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
(OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
