"""Reviewed execution configurations layered on the accepted V2 gateway.

A configuration is a versioned research input, not a legal-pool certification.
Approval is a source-controlled exact-byte allowlist; no user supplied hash can
authorize a configuration. Future profiles need separate reviewed native support.
"""
import json
from pathlib import Path
from types import MappingProxyType

from format_match_v2 import VerifiedGateway, FormatRejected, PROFILE_SHA, REGISTRY_SHA, ENGINE_SHA, digest

APPROVED = MappingProxyType({
    "standard-2026-11-23-research-v1": "50f56e25a2524ce5ed3c2971f49ccf605790f4a9746927fb743c8d641bb48811",
    "hypothetical-exclude-ogs-v1": "6bfe6f07e66c1b373df3d3bd6e8fdf1025f1a1bfd9f130f0b640a562ce3e511f",
})
CONFIG_ROOT = Path(__file__).resolve().parents[1] / "rulesets" / "configurations"


def load_configuration(configuration_id, root=CONFIG_ROOT):
    if configuration_id not in APPROVED:
        raise FormatRejected("unapproved execution configuration")
    raw = (Path(root) / (configuration_id + ".json")).read_bytes()
    expected = APPROVED[configuration_id]
    if digest(raw) != expected:
        raise FormatRejected("unapproved configuration bytes")
    config = json.loads(raw)
    if (config["configuration_id"] != configuration_id
            or config["schema_version"] != 1
            or config["profile_sha256"] != PROFILE_SHA
            or config["registry_sha256"] != REGISTRY_SHA
            or config["engine_sha256"] != ENGINE_SHA
            or config["official_full_legality_certified"] is not False
            or config["classification"] not in {"dated_ban_snapshot_research","hypothetical_set_filter"}
            or not config["allowed_sets"] or len(set(config["allowed_sets"])) != len(config["allowed_sets"])):
        raise FormatRejected("configuration inconsistent with pinned native gateway")
    return config, expected


class ApprovedGateway(VerifiedGateway):
    def __init__(self, engine, registry, profile, configuration_id):
        config, config_hash = load_configuration(configuration_id)
        self._configuration = MappingProxyType({
            "configuration_id": configuration_id,
            "configuration_sha256": config_hash,
            "configuration_classification": config["classification"],
            "configuration_scope": config["scope"],
        })
        super().__init__(engine, registry, profile, tuple(config["allowed_sets"]),
                         tuple(config["rune_exempt_ids"]))

    def provenance(self):
        return {**super().provenance(), **self._configuration}
