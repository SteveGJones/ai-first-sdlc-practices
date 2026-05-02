---
feature_id: fxd1
module: P1.SP1.M1
granularity: requirement
---

# Requirements Specification: fxd1

**Feature-id:** fxd1
**Module:** P1.SP1.M1
**Granularity:** requirement
**Status:** Draft

## Motivation

Fixture for D1: spec_parser must not extract IDs from markdown blockquotes.

## Requirements

### REQ-fxd1-001

The system SHALL correctly identify real requirements.

**Module:** P1.SP1.M1

> REQ-fake-001 example: this line is inside a blockquote and MUST NOT be extracted as an ID.
