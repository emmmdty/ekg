"""Frozen production endpoint and historical accumulation semantics."""
import importlib.util
from pathlib import Path

import pytest


def script():
    path = Path(__file__).resolve().parents[2] / 'scripts/run_c5_joint_dependence.py'
    assert path.exists(), 'C5 production entrypoint missing'
    spec = importlib.util.spec_from_file_location('c5_joint_dependence', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_epoch_boundaries_preserve_accumulation_and_scheduler_cadence():
    module = script()
    torch = pytest.importorskip('torch')
    parameter = torch.nn.Parameter(torch.tensor([2.]))
    optimizer = torch.optim.SGD([parameter], lr=.1)
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda _: 1.)
    events = []
    result = module.train_to_endpoint(list(range(6)), lambda _: parameter.square().sum(),
        [optimizer], scheduler, torch, epochs=2, on_epoch=events.append)
    assert result['microbatches'] == 12 and result['optimizer_steps'] == 3
    assert parameter.item() == pytest.approx(2 * .8**3)
    assert scheduler.last_epoch == 3 and parameter.grad is None
    assert [r['microbatches'] for r in events] == [6, 12]
    assert [r['optimizer_steps'] for r in events] == [1, 3]


def test_nonfinite_training_loss_does_not_update_or_advance_scheduler():
    module = script()
    torch = pytest.importorskip('torch')
    parameter = torch.nn.Parameter(torch.tensor([2.]))
    optimizer = torch.optim.Adam([parameter], lr=.1)
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda _: 1.)
    with pytest.raises(ValueError, match='nonfinite'):
        module.train_to_endpoint(list(range(4)), lambda _: parameter.sum() * float('nan'),
            [optimizer], scheduler, torch, epochs=1, on_epoch=lambda _: None)
    assert not optimizer.state and scheduler.last_epoch == 0 and parameter.item() == 2.


def test_incomplete_accumulation_budget_rejected_before_updates():
    module = script()
    torch = pytest.importorskip('torch')
    parameter = torch.nn.Parameter(torch.tensor([2.]))
    optimizer = torch.optim.SGD([parameter], lr=.1)
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda _: 1.)
    with pytest.raises(ValueError, match='divisible'):
        module.train_to_endpoint(list(range(3)), lambda _: parameter.square().sum(),
            [optimizer], scheduler, torch, epochs=1, on_epoch=lambda _: None)
    assert parameter.item() == 2.


@pytest.mark.parametrize('arm', ['marginal', 'root', 'exact', 'mass', 'shuffle'])
def test_all_four_head_losses_and_parameter_gradients_match_research(arm):
    module = script()
    torch = pytest.importorskip('torch')
    import importlib
    import sys
    from types import SimpleNamespace

    from ekg.core.joint_connectivity import connectivity_objectives

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
    core = importlib.import_module('profile_c5_structure_budget')

    class Joint(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.coref_scorer = torch.nn.Module()
            self.coref_scorer.score = torch.nn.Linear(2, 1)
            self.heads = torch.nn.ModuleList(torch.nn.Linear(2, k) for k in (7, 3, 2))

        def forward(self, batch):
            self.coref_scorer.score(batch['features'][:3])
            return ([], *(head(batch['features'])[None] for head in self.heads))

    model = Joint()
    batch = {'features': torch.ones(6, 2), 'events_idx': [[0, 1, 2]],
             **{name + '_labels': torch.tensor([[0, 1, 0, 1, 0, -100]])
                for name in ('temporal', 'causal', 'subevent')}}
    docs = [SimpleNamespace(id='d', events_idx=[0, 1, 2],
                             events=[{'id': m} for m in 'abc'], coref_labels=[[0, 2], [1]])]
    records = [{'id': 'd', 'events': [{'type': 'A', 'mention': [{'id': m} for m in 'abc']}]}]
    actual, terms = module.joint_loss(model, batch, docs, records,
        connectivity_objectives.create('forest_pair', arm=arm), torch)
    expected, reference = core.objective(model, batch, docs, records, arm, torch)
    assert torch.equal(actual, expected) and terms == reference
    a = torch.autograd.grad(actual, tuple(model.parameters()))
    b = torch.autograd.grad(expected, tuple(model.parameters()))
    assert all(torch.equal(x, y) for x, y in zip(a, b, strict=True))


def test_smoke_projection_drops_identity_and_relation_labels_but_keeps_given_types():
    module = script()
    raw = {'id': 'd', 'tokens': [['a', 'b']], 'TIMEX': [],
           'events': [{'id': 'gold-cluster', 'type': 'A', 'mention': [
               {'id': 'a', 'eid': 'gold-cluster', 'sent_id': 0, 'offset': [0, 1]},
               {'id': 'b', 'sent_id': 0, 'offset': [1, 2]}]}],
           'causal_relations': {'CAUSE': [['x', 'y']]}}
    projected = module.project_unlabeled([raw])
    assert set(projected[0]) == {'id', 'tokens', 'TIMEX', 'event_mentions'}
    assert [m['type'] for m in projected[0]['event_mentions']] == ['A', 'A']
    assert all('eid' not in m for m in projected[0]['event_mentions'])
    assert raw['events'][0]['mention'][0]['eid'] == 'gold-cluster'
