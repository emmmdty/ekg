"""Dataset loaders that normalize public relation data into EKG contracts."""

from ekg.relations.data.ccks_causal import load_ccks_causal
from ekg.relations.data.maven_arg import ArgumentDocument, TriggerCandidate, load_maven_arg
from ekg.relations.data.maven_ere import RelationDocument, load_maven_ere
from ekg.relations.data.maven_fact import (
    FACTUALITY_LABELS,
    FactualityDocument,
    FactualityMention,
    load_maven_fact,
)

__all__ = [
    "RelationDocument",
    "load_maven_ere",
    "load_ccks_causal",
    "ArgumentDocument",
    "TriggerCandidate",
    "load_maven_arg",
    "FACTUALITY_LABELS",
    "FactualityDocument",
    "FactualityMention",
    "load_maven_fact",
]
