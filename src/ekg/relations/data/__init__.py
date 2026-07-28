"""Dataset loaders that normalize public relation data into EKG contracts."""

from ekg.relations.data.ccks_causal import load_ccks_causal
from ekg.relations.data.maven_arg import ArgumentDocument, TriggerCandidate, load_maven_arg
from ekg.relations.data.maven_ere import RelationDocument, load_maven_ere

__all__ = [
    "RelationDocument",
    "load_maven_ere",
    "load_ccks_causal",
    "ArgumentDocument",
    "TriggerCandidate",
    "load_maven_arg",
]
