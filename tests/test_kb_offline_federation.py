"""Federation query tests. kb-offline M2b (#211)."""
from __future__ import annotations

from sdlc_knowledge_base_scripts.audit import VALID_EVENT_TYPES


def test_cross_library_query_is_a_valid_event_type():
    assert "cross_library_query" in VALID_EVENT_TYPES
