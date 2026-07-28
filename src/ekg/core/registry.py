"""A tiny name -> factory registry that keeps method swaps framework-free.

Each pluggable component (relation extractor, consistency solver, forecaster)
owns a `Registry`. Implementations register under a string name; pipelines and
configs select one by name. Adding a neural upgrade next to a heuristic
baseline is a one-line `@registry.register("name")` — no caller changes.

    relation_extractors = Registry("relation_extractor")

    @relation_extractors.register("heuristic")
    class HeuristicRelationExtractor: ...

    extractor = relation_extractors.create("heuristic", **cfg)
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Generic, TypeVar, cast

__all__ = ["Registry"]

T = TypeVar("T")
# Bound to the *decorated* object so `@registry.register(...)` over a class keeps
# that class's type (a plain `Callable[..., T]` return would demote it to a
# function and break attribute/classmethod inference at every call site).
F = TypeVar("F", bound=Callable[..., Any])


class Registry(Generic[T]):
    """A named collection of factories producing components of type ``T``."""

    def __init__(self, kind: str) -> None:
        self.kind = kind
        self._factories: dict[str, Callable[..., T]] = {}

    def register(self, name: str) -> Callable[[F], F]:
        """Decorator: register a class/factory under ``name``."""

        def decorator(factory: F) -> F:
            if name in self._factories:
                raise KeyError(f"{self.kind!r} already has an implementation named {name!r}")
            self._factories[name] = cast(Callable[..., T], factory)
            return factory

        return decorator

    def create(self, name: str, **kwargs: object) -> T:
        """Instantiate the implementation registered under ``name``."""
        if name not in self._factories:
            raise KeyError(
                f"unknown {self.kind} {name!r}; available: {sorted(self._factories)}"
            )
        return self._factories[name](**kwargs)

    def available(self) -> list[str]:
        return sorted(self._factories)

    def __contains__(self, name: str) -> bool:
        return name in self._factories
