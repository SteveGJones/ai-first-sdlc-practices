"""Ratified eval thresholds (issue #211, spec eval section). Safety floors are
deterministic guarantees (= 1.0). Model-quality numbers are the M1 gate, ratified at
M0 exit."""
from __future__ import annotations

# Safety floors (deterministic-code guarantees)
INVALID_MUTATION_REJECTION = 1.0
CITATION_VALIDITY = 1.0
FEDERATION_ATTRIBUTION = 1.0
POST_REPAIR_JSON_VALIDITY = 1.0

# Model-quality thresholds (release-suite gate before Ollama default)
CITATION_ENTAILMENT = 0.98
FACT_RECALL = 0.85
ROUTING_RECALL = 0.90
ROUTING_PRECISION = 0.80
ABSTENTION_PRECISION = 0.95
ABSTENTION_RECALL = 0.90
FIRST_PASS_JSON_VALIDITY = 0.95

# 3x-run reproducibility cap (M1c-2): a model-quality metric passes only if its
# per-metric sample stddev across the 3 pinned runs stays at/below this.
MAX_METRIC_STDDEV = 0.05
