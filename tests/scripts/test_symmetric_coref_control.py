"""Verify fixed directional averaging, type-matched controls and true scorer parity."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def script():
    path = ROOT / 'scripts/run_symmetric_coref_control.py'
    assert path.exists(), 'symmetric control entrypoint missing'
    spec = importlib.util.spec_from_file_location('symmetric_control', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_average_is_on_logits_and_keeps_dummy_and_candidate_shape():
    forward = [[], [-2], [3, 1]]
    reverse = [[], [4], [-1, -3]]
    result = script().combine_logits(forward, reverse)
    assert result == [[0], [1, 0], [1, -1, 0]]
    assert forward == [[], [-2], [3, 1]]


@pytest.mark.parametrize('reverse', [[[], []], [[], [float('nan')]], [[], [1, 2]]])
def test_invalid_score_population_or_values_fail(reverse):
    with pytest.raises(ValueError):
        script().combine_logits([[], [1]], reverse)


def test_negative_control_cannot_mix_types_or_dummy_scores():
    ids = ['a', 'b', 'c', 'd']
    types = {'a': 'T', 'b': 'T', 'c': 'U', 'd': 'T'}
    reverse = [[], [10], [20, 30], [40, 50, 60]]
    shuffled = script().shuffle_reverse(ids, reverse, types)
    assert sorted([shuffled[1][0], shuffled[3][0], shuffled[3][1]]) == [10, 40, 50]
    assert shuffled[2] == [20, 30]
    assert shuffled[3][2] == 60
    assert reverse == [[], [10], [20, 30], [40, 50, 60]]
    assert shuffled == script().shuffle_reverse(ids, reverse, types)


def test_real_torch_directional_head_swaps_only_the_two_mention_blocks():
    torch = pytest.importorskip('torch')
    head = torch.nn.Linear(6, 1, bias=False)
    with torch.no_grad():
        head.weight.copy_(torch.tensor([[1., 0., 10., 0., 0., 0.]]))
        forward, reverse = script().directional_logits(
            head, torch.tensor([[1., 2.], [3., 4.], [5., 6.]]), torch)
    assert forward == [[], [13.0], [15.0, 35.0]]
    assert reverse == [[], [31.0], [51.0, 53.0]]


def test_actual_official_head_forward_matches_original_probabilities(monkeypatch):
    import importlib
    import json

    torch = pytest.importorskip('torch')
    source = Path(json.loads((ROOT / 'configs/c5_official_cpu_cache_20261013.json').read_text())[
        'source_root']).resolve()
    if not source.exists():
        pytest.skip('original scorer stays on gpu-4090')
    monkeypatch.syspath_prepend(str(source))
    monkeypatch.setattr(torch.cuda, 'is_available', lambda: False)
    module = importlib.import_module('src.model')
    torch.manual_seed(13)
    scorer = module.CorefPairScorer(embed_dim=2).eval()
    embed = torch.tensor([[1., 2.], [3., 4.], [5., 6.]])
    with torch.no_grad():
        forward, reverse = script().directional_logits(scorer.score, embed, torch)
        original = scorer([embed], [[0, 1, 2]])[0]
        for i, row in enumerate(forward):
            expected = torch.softmax(torch.tensor([*row, 0.0]), dim=0)
            assert torch.equal(expected, original[i, :i + 1])
        first_reverse = scorer.score(torch.cat((embed[0], embed[1], embed[0] * embed[1])))
    # Single-row and batched GEMMs can differ in the last bits. The production
    # forward-cache comparison remains exact for the same batched operation.
    assert reverse[1] == pytest.approx(first_reverse.reshape(-1).tolist(), abs=1e-6)
