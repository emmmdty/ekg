"""Validate the full antecedent universe and exact strong-anchor parity."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def script():
    spec = importlib.util.spec_from_file_location(
        "export_official_coref_cpu", ROOT / "scripts/export_official_coref_cpu.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_complete_triangular_candidates_include_dummy():
    row = {"id": "d", "mentions": ["a", "b", "c"],
           "probabilities": [[1.0], [0.6, 0.4], [0.2, 0.5, 0.3]],
           "pair_logits": [[], [0.4054651081081644], [-0.4054651081081643, 0.5108256237659907]]}
    script().validate_cache_document(row)


@pytest.mark.parametrize("probabilities", [
    [[1.0], [0.6]], [[1.0], [0.6, 0.5]], [[1.0], [float('nan'), 0.4]],
])
def test_missing_or_invalid_candidates_fail(probabilities):
    with pytest.raises(ValueError, match="probability"):
        script().validate_cache_document({"id": "d", "mentions": ["a", "b"],
                                           "probabilities": probabilities,
                                           "pair_logits": [[], [0.4054651081081644]]})


def test_probabilities_must_match_original_logits():
    with pytest.raises(ValueError, match="logit"):
        script().validate_cache_document({"id": "d", "mentions": ["a", "b"],
                                           "probabilities": [[1.0], [0.6, 0.4]],
                                           "pair_logits": [[], [2.0]]})


def test_anchor_parity_does_not_accept_a_close_score():
    original = {"id": "d", "coreference": [["a", "b"], ["c"]]}
    script().require_parity(original, [["b", "a"]], ["a", "b", "c"])
    with pytest.raises(ValueError, match="parity"):
        script().require_parity(original, [["a", "c"]], ["a", "b", "c"])
    with pytest.raises(ValueError, match="mention"):
        script().require_parity(original, [["a", "unknown"]], ["a", "b", "c"])


def test_smoke_dependency_requires_matching_config_and_hashes(tmp_path):
    import json

    status = tmp_path / 'status.json'
    status.write_text(json.dumps({'status': 'complete', 'config_sha256': 'different',
                                 'artifact_sha256': {}}))
    with pytest.raises(ValueError, match='smoke'):
        script().require_smoke(tmp_path, 'frozen')


def test_export_scope_rejects_gold_clusters():
    with pytest.raises(ValueError, match='unlabeled'):
        script().validate_records([{'id': 'd', 'events': []}], {'d'})


def test_unlabeled_population_matches_exact_candidate_digest():
    import hashlib

    record = {'id': 'd', 'event_mentions': [{'id': 'a', 'sent_id': 0, 'offset': [0, 1]},
                                          {'id': 'b', 'sent_id': 0, 'offset': [1, 2]}],
              'TIMEX': [{'id': 'TIMEX_t'}]}
    result = script().input_population({'d': record})
    expected = hashlib.sha256(b'd::a->d::b\nd::b->d::a\n').hexdigest()
    assert result == {'candidate_id_digest': expected,
                      'documents': 1, 'event_mentions': 2, 'timex': 1, 'relation_pairs': 2}


def test_real_official_head_exports_event_only_candidates_on_cpu(monkeypatch):
    import importlib
    import json

    torch = pytest.importorskip('torch')
    source = Path(json.loads((ROOT / 'configs/c5_official_cpu_cache_20261013.json').read_text())[
        'source_root']).resolve()
    if not source.exists():
        pytest.skip('frozen upstream workspace stays on gpu-4090')
    monkeypatch.syspath_prepend(str(source))
    monkeypatch.setattr(torch.cuda, 'is_available', lambda: False)
    upstream = importlib.import_module('src.model')
    assert Path(upstream.__file__).resolve() == source / 'src/model.py'
    torch.manual_seed(13)
    scorer = upstream.CorefPairScorer(embed_dim=2).eval()
    captured = []
    hook = scorer.score.register_forward_hook(
        lambda module, inputs, result: captured.append(result.detach().flatten().tolist()))
    try:
        with torch.no_grad():
            probs = scorer([torch.tensor([[1., 2.], [9., 9.], [3., 4.]]),
                            torch.tensor([[5., 6.]])], [[0, 2], [0]])
        assert len(captured) == 1
        assert probs[0].device.type == 'cpu'
        assert probs[0].shape == (2, 2)
        assert probs[1].tolist() == [[1.0]]
        script().validate_cache_document({'id': 'd', 'mentions': ['a', 'c'],
                                           'probabilities': [probs[0][0, :1].tolist(),
                                                             probs[0][1, :2].tolist()],
                                           'pair_logits': [[], captured[0]]})
    finally:
        hook.remove()
