import hashlib
import importlib
import logging

import pytest


def module():
    return importlib.import_module("ekg.relations.ergo_training")


def test_binary_log_meter_preserves_upstream_swapped_positive_behavior_and_resets():
    meter = module().BinaryPrefixMeter()
    logger = logging.getLogger("ergo-test")
    gold, predicted = [1, 2, 0], [2, 0, 1]
    assert meter(gold, predicted, logger) == (0.5, 0.5, 0.5)
    gold.extend([0, 2])
    predicted.extend([0, 2])
    assert meter(gold, predicted, logger) == pytest.approx((2 / 3, 2 / 3, 2 / 3))
    assert meter(gold, predicted, logger) == pytest.approx((2 / 3, 2 / 3, 2 / 3))
    assert meter([0], [0], logger) == (0.0, 0.0, 0.0)
    with pytest.raises(ValueError, match="length"):
        meter([1], [], logger)


def test_epoch_loader_executes_only_pinned_function_without_missing_processor_import(tmp_path):
    torch = pytest.importorskip("torch")
    path = tmp_path / "train.py"
    path.write_text("import missing_processor_esl\nraise RuntimeError('must not run')\n"
                    "def train_epoch(args, model, train_loader, optimizer, scheduler):\n"
                    "    return torch.add(model, 3)\n")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    epoch = module().load_train_epoch(path, digest, module().BinaryPrefixMeter())
    assert epoch(None, torch.tensor(2), None, None, None).item() == 5
    path.write_text(path.read_text().replace('model, 3', 'model, 4'))
    with pytest.raises(ValueError, match="source drift"):
        module().load_train_epoch(path, digest, module().BinaryPrefixMeter())
