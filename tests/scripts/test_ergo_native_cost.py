import hashlib
import importlib.util
from pathlib import Path

import pytest


def script():
    path = Path("scripts/profile_ergo_native_cost.py")
    spec = importlib.util.spec_from_file_location("ergo_cost", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_optimizer_loader_keeps_class_body_and_rejects_source_drift(tmp_path):
    pytest.importorskip("torch")
    pytest.importorskip("transformers")
    source = tmp_path / "optimization.py"
    source.write_text("raise RuntimeError('unrelated module code must not run')\n"
                      "class AdamW(Optimizer):\n"
                      "    marker = 17\n"
                      "    def step(self, closure=None):\n"
                      "        return self.marker\n")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    cls = script().load_legacy_adamw(source, digest)
    assert cls.marker == 17
    source.write_text(source.read_text().replace("17", "18"))
    with pytest.raises(ValueError, match="optimizer source"):
        script().load_legacy_adamw(source, digest)


def test_parameter_identity_ignores_only_zero_sign_without_mutating_model():
    torch = pytest.importorskip("torch")
    layer = torch.nn.Linear(2, 1, bias=False)
    with torch.no_grad():
        layer.weight.copy_(torch.tensor([[0.0, 2.0]]))
    before = script().parameter_identities(layer)
    with torch.no_grad():
        layer.weight[0, 0] = -0.0
    after = script().parameter_identities(layer)
    assert torch.signbit(layer.weight[0, 0]).item()
    assert before["raw_sha256"] != after["raw_sha256"]
    assert before["numeric_sha256"] == after["numeric_sha256"]
    assert after["negative_zero_values"] == 1
    with torch.no_grad():
        layer.weight[0, 1] = 2.01
    assert script().parameter_identities(layer)["numeric_sha256"] != before["numeric_sha256"]


def feature():
    return {
        "id": "d", "mention_ids": ["a", "b"],
        "enc_input_ids": [0, 50265, 5, 50266, 50265, 7, 50266, 2],
        "enc_mask_ids": [1] * 8, "global_attention_mask": [1, 0, 0, 0, 0, 0, 0, 1],
        "t1_pos": [1, 4], "t2_pos": [4, 1],
    }


def test_real_model_inputs_use_complete_pairs_and_bool_original_mask():
    torch = pytest.importorskip("torch")
    packed = script().model_inputs(feature(), [0, 2], torch.device("cpu"))
    assert packed["mh_self_attention_mask"].tolist() == [[[True, False], [False, True]]]
    assert packed["mh_self_attention_mask"].dtype == torch.bool
    assert packed["enc_input_ids"].shape == (1, 8)
    assert packed["target"] == [[0, 2]]
    assert packed["t1_pos"] == [[1, 4]]
    with pytest.raises(ValueError, match="candidate"):
        script().model_inputs(feature(), [0], torch.device("cpu"))
    bad = feature()
    bad["t1_pos"] = [2, 4]  # A word is not an event start marker.
    with pytest.raises(ValueError, match="marker"):
        script().model_inputs(bad, [0, 2], torch.device("cpu"))


def test_trim_only_trailing_padding_preserves_all_words_markers_pairs_and_input():
    f = feature()
    padded = {**f, "enc_input_ids": f["enc_input_ids"] + [1] * 8,
              "enc_mask_ids": [1] * 8 + [0] * 8,
              "global_attention_mask": f["global_attention_mask"] + [0] * 8}
    trimmed = script().trim_trailing_padding(padded)
    assert trimmed == f
    assert len(padded["enc_input_ids"]) == 16
    assert script().trim_trailing_padding(f) == f
    bad = {**padded, "enc_input_ids": f["enc_input_ids"] + [999] + [1] * 7}
    with pytest.raises(ValueError, match="padding"):
        script().trim_trailing_padding(bad)

    bad = {**padded, "global_attention_mask": f["global_attention_mask"] + [1] + [0] * 7}
    with pytest.raises(ValueError, match="padding"):
        script().trim_trailing_padding(bad)


def test_canonical_cost_cannot_silently_trim_or_claim_padding_parity():
    f = feature()
    config = {"schema_version": "ekg.ergo_native_cost.v3", "padding_policy": "retain_all_4096",
              "padding_parity_required": False}
    assert script().execution_feature(f, config) is f
    for wrong in ({**config, "padding_parity_required": True},
                  {**config, "padding_policy": "drop_only_verified_trailing_pad"},
                  {**config, "schema_version": "unknown"}):
        with pytest.raises(ValueError, match="padding contract"):
            script().execution_feature(f, wrong)
