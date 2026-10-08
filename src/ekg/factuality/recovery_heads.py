"""Matched head controls, torch-lazy; these are diagnostics, not new methods."""

from ekg.core.registry import Registry

HEADS = ("linear", "tanh5")
head_factories = Registry("factuality_head")


def validate_head(name: str) -> str:
    if name not in HEADS:
        raise ValueError(f"unknown factuality head {name!r}; expected {HEADS}")
    return name


@head_factories.register("linear")
def linear(*, width: int, labels: int):
    from torch import nn

    return nn.Linear(width, labels)


@head_factories.register("tanh5")
def tanh5(*, width: int, labels: int):
    from torch import nn

    return nn.Sequential(nn.Linear(width, 5), nn.Tanh(), nn.Linear(5, labels))


def build_head(name: str, width: int, labels: int):
    validate_head(name)
    if width < 1 or labels < 1:
        raise ValueError("head dimensions must be positive")
    return head_factories.create(name, width=width, labels=labels)
