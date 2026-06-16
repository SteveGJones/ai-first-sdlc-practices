# kb-offline M3c-3 — shareable-fingerprint "find who to ask" discovery (design)

**EPIC:** #211 kb-offline (LangGraph+Ollama backend for `sdlc-knowledge-base`). Branch `feature/211-kb-offline-langgraph` (one accumulating branch, no PR until deliberate).

**Milestone:** M3c-3 — the cross-org, privacy-preserving discovery layer that completes M3c (M3c-1 RRF+compat primitive ✓, M3c-2 accelerated federated query ✓).

**One-line goal:** A library owner can publish a shareable embedding *fingerprint* that lets another organisation discover *that the library covers a subject* — and *who to ask about it* — **without any access to the underlying content, filenames, or structured metadata.** Embeddings are the privacy-preserving discovery layer; reasoning/assembly (shelf-select, synthesis) stays where access exists and is untouched here.

---

## 1. Scope

**In scope (the full shareable-fingerprint exchange):**
- An **export** side: turn an already-built `EmbeddingStore` into a portable `*.kbfp.json` artifact, at a publisher-chosen privacy **tier**.
- A **discover** side: embed a question once, score one or more received fingerprints, return a ranked "who to ask" list.
- Two privacy tiers, **chosen per-library by the publisher**: coarse (k-means centroids) and page-level (bag of page vectors, page_ids stripped).
- Two CLI subcommands (`fingerprint export`, `discover`) over a new pure module `scripts/fingerprint.py`.

**Out of scope (later milestones / explicitly deferred):**
- A separate `fingerprint import`/registry command — receiving a fingerprint is just dropping a file in a directory (YAGNI for v1).
- Calibrated coverage **bands** (strong/weak/none) — deferred until discovery has its own labelled eval; v1 reports raw scores (see §4).
- Any content read, shelf reasoning, or synthesis on the discover side — discovery is the pure embeddings layer.
- M3d semantic cross-library conflict lint (separate milestone).
- Cross-embedding-model bridging — vectors from different models are mathematically incomparable; incompatible fingerprints are rejected, not reconciled.

---

## 2. Architecture

**One new module: `plugins/sdlc-knowledge-base/scripts/fingerprint.py`.** Pure functions + numpy + file IO. No LangGraph, no graph, no backend *at rest* (the discover side takes a backend only to embed the question once).

```
EXPORT (no backend)                          DISCOVER (backend embeds question once)
  EmbeddingStore.load(library)                 backend.embed([question]) -> qvec
    -> freshness gate (corpus_hash)            load_fingerprint(path) for each source
    -> tier "coarse": _kmeans -> centroids       -> data_sha256 verify (reject+warn)
       tier "page":   page vectors, ids dropped  -> compatible(qprov, fp.prov) (reject+warn)
    -> write *.kbfp.json                         -> score_fingerprint(qvec, fp)
                                               rank by score desc -> who-to-ask list
```

**Module interface (`fingerprint.py`):**
- `export_fingerprint(store, *, tier, manifest, clusters=8, weights=True, seed=7) -> dict` — builds the artifact dict (caller writes it). `seed=7` matches the eval-pin convention and makes coarse exports reproducible.
- `write_fingerprint(path, artifact) -> None` / `load_fingerprint(path) -> Fingerprint | None` — IO + integrity/shape validation; `None` on corruption/sha-mismatch/unknown-version (caller warns and skips).
- `_kmeans(vectors, k, seed) -> (centroids, weights)` — Lloyd's k-means with seeded init, numpy only, **deterministic** (same input + seed → identical centroids); each output centroid re-L2-normalized.
- `score_fingerprint(qvec, fp, *, hit_threshold=0.5) -> ScoreResult` — `{score, tier, n_hits|None}`.
- `discover(qvec, fingerprints, *, min_score=0.0, hit_threshold=0.5, top=None) -> [DiscoverHit]` — filters incompatible, scores, ranks.

`Fingerprint` and the result rows are small typed structures (pydantic models consistent with the rest of kb-offline `contracts.py`, or plain dataclasses if no validation is needed — implementer's call, matching surrounding style).

---

## 3. The `*.kbfp.json` interchange artifact

A single self-contained, human-auditable file (designed to be emailed / dropped in a shared drive):

```json
{
  "version": 1,
  "tier": "coarse",
  "manifest": {
    "handle": "acme-safety",
    "owner": "Acme Safety Engineering",
    "contact": "safety-kb@acme.example"
  },
  "provenance": {
    "model": "nomic-embed-text",
    "dims": 768,
    "normalization": "l2"
  },
  "vectors": [[0.0123, -0.0456, ...], ...],
  "weights": [12, 5, 31],
  "data_sha256": "<hex over the canonical serialization of `vectors`>"
}
```

Field rules:
- `version` (int) — format version; unknown version → `load_fingerprint` returns `None` (reject+warn).
- `tier` — `"coarse"` or `"page"`.
- `manifest` — `{handle, owner, contact}`; `contact` may be `null`. This is the entire "who to ask" payload returned by discovery.
- `provenance` — `{model, dims, normalization}`. **No `corpus_hash`** (it would leak change-tracking and is not needed; compatibility excludes it — see §5/M3c-1 `compatible`).
- `vectors` — nested float arrays, **all rows L2-normalized**. For `coarse`: K centroids. For `page`: N page vectors, **page_ids stripped entirely** (an ordered/unordered array of vectors, no identifiers).
- `weights` — **coarse tier only**; integer pages-per-centroid (improves ranking and tie-breaks). Omitted entirely when the publisher passes `--no-weights`, and absent for page tier.
- `data_sha256` — hex SHA-256 over a **canonical serialization of `vectors`** (e.g. `json.dumps(vectors, separators=(",",":"))` encoded UTF-8 — the exact canonicalization is fixed in the implementation and re-derived identically on load). Tamper/truncation evidence; mismatch → reject+warn. (The canonical form must be deterministic and independent of surrounding whitespace.)

**Encoding decision:** nested JSON float arrays (not base64). Float32→float64 (`tolist`) is exact widening; Python's shortest-repr JSON guarantees `loads(dumps(x)) == x` for finite float64; narrowing float64→float32 on load recovers the original float32 bit-for-bit. So nested arrays round-trip **losslessly** — fidelity is not a differentiator, and readability/auditability (a receiving org can open the file and confirm it is *only* normalized vectors, no opaque payload) wins for a cross-org trust artifact. Size cost (~3× base64) is acceptable: tier-i is tiny; tier-ii is a few MB at most.

---

## 4. Coverage scoring & ranking

The discoverer embeds the question once → `qvec`, L2-normalized. Because everything is L2-normalized, **cosine = dot product**.

Per compatible fingerprint:
- **page tier:** `score = max over page vectors of dot(qvec, page_vec)` (best single-page match). `n_hits = #{ page vectors with dot ≥ hit_threshold }` (default `hit_threshold = 0.5`).
- **coarse tier:** `score = max over centroids of dot(qvec, centroid)`. `n_hits = None` (no pages to count; output shows `—`).

**Ranking:** by `score` descending; `--top N` truncates; `--min-score F` filters (default `0.0` = show all ranked).

**Comparability caveat (stated, not hidden):** coarse and page scores are *not* on the same scale — a centroid is an average, so its cosine to a query is systematically lower than the best individual page's cosine in that cluster. The output therefore **always shows the tier** so a `0.55 (coarse)` is read differently from a `0.55 (page)`. v1 deliberately does **not** introduce calibrated cross-tier bands, because there is no labelled cross-org ground truth to calibrate cutoffs against (unlike M3b's recall@k, which had the eval suite). `hit_threshold` is a **display heuristic for the `n_hits` column, not a gate**, and is configurable via `--hit-threshold`.

---

## 5. Privacy threat model

**Protected (cannot be recovered from a fingerprint):**
- Document **content** — embeddings are one-way; text cannot be reconstructed.
- **Filenames / page_ids** — dropped in both tiers (page tier ships an identifier-free vector array; coarse ships only centroids).
- **Shelf / structured metadata** (layers, confidence, facts, cross-references) — never exported.
- **Change-tracking** — `corpus_hash` is omitted.

**Disclosed by design:**
- That the library's vector space has regions near a given query — i.e. *that it covers a subject* (the intended capability).
- Approximate corpus **size**: page-tier discloses the page count (vector array length); coarse-tier discloses only coarse cluster `weights` (and the publisher may `--no-weights` to suppress even that).
- The published `{handle, owner, contact}`.

**Residual risk (acknowledged):** an adversary with the *same embedding model* and a large probe-question set can map *which topics* a library covers (this is the feature, not a leak) and can estimate corpus size from a page-tier fingerprint. **Tier coarse exists precisely for publishers who will not disclose per-page geometry or size** — it is the privacy-conservative option, page tier the precision-favoring one. The publisher chooses per library.

**Compatibility gate (hard):** discovery reuses M3c-1 `fusion.compatible(prov_a, prov_b)` (match on `model` + `dims` + `normalization`; `corpus_hash` excluded). Cross-model vectors are incomparable, so an incompatible fingerprint is **rejected with a stderr warning**, never scored and never crashes the run. Cross-org discovery therefore requires both parties to use the same embedding model (e.g. `nomic-embed-text`); this is an inherent constraint, surfaced clearly, not a defect.

---

## 6. CLI surface

Two new subcommands in `kb_offline_cli.py`, thin wrappers over `fingerprint.py`.

### `kb-offline fingerprint export`
Turns a library's existing `EmbeddingStore` into a `.kbfp.json`. **No backend / no Ollama** — vectors already exist.
- `--library <dir>` (default `library`).
- `--tier coarse|page` — **required**, no default (the privacy choice must be explicit).
- `--out <path>` (default `<handle>.kbfp.json`).
- `--handle <str>` (default: library dir name), `--owner <str>`, `--contact <str>` (optional, nullable).
- `--clusters K` (coarse only, default `8`, clamped to page count when pages < K).
- `--no-weights` (coarse only — omit the `weights` field).
- **Freshness gate:** refuse if the store's `corpus_hash` ≠ a fresh `chunk_pages` hash (publishing a stale fingerprint misrepresents coverage); `--allow-stale` overrides. Refuse with a clear message ("run `kb-offline index` first") when no store exists.

### `kb-offline discover "<question>"`
Embeds the question once (needs `--backend`, default `ollama`), scores received fingerprints, prints the ranked who-to-ask list.
- Sources: repeatable `--fingerprint <path>` and/or `--fingerprints <dir>` (scans `*.kbfp.json`; default dir `~/.sdlc/fingerprints/`). Receiving = dropping a file there; no `import` command in v1.
- `--min-score <float>` (default `0.0`), `--top <N>` (default unlimited), `--hit-threshold <float>` (default `0.5`).
- Per fingerprint: `load_fingerprint` → `data_sha256` verify (mismatch → reject+warn) → `compatible(qprov, fp.prov)` gate (incompatible → reject+warn) → score.
- Output, ranked by score desc: `handle · owner · contact · score · tier · [n_hits pages | —]`.
- Empty source set / all rejected / no coverage → a clear message, **exit 0** (discovery finding nothing is a valid result, not an error).
- A test seam mirroring M3c-2's `library_specs_override` / `backend_override` (e.g. `fingerprints_override`) for CLI tests without real files where convenient.

---

## 7. Testing

All unit tests on **`FakeBackend` / pure numpy** (no Ollama). Export needs no backend; discover's only backend call is the single question-embed.

- **Round-trip fidelity:** export → `load_fingerprint` → vectors recover **bit-exact float32**.
- **Privacy (first-class):** the written artifact contains **no page_ids/filenames, no content, no `corpus_hash`, no shelf text** — asserted explicitly for both tiers.
- **Coarse tier:** seeded k-means deterministic (same input → same centroids); `K` clamps to page count; `weights` sum = page count; `--no-weights` omits the field.
- **Page tier:** vector count = page count; identifiers absent.
- **Integrity + compat:** tampered vector → `data_sha256` mismatch → reject; unknown `version` → reject; incompatible model/dims/normalization → reject+warn (no crash); mixed set scores only compatible fingerprints.
- **Scoring/ranking:** controlled vectors → max-cosine correct; `n_hits` counts pages ≥ `hit_threshold`; coarse score = max over centroids; ranking order; `--min-score`/`--top` honored; behavioral sanity (on-topic question ranks the relevant library above an off-topic one).
- **CLI:** export writes expected fields, refuses stale (with `--allow-stale` override), clear message when no store; discover prints the ranked line and an all-rejected/empty set → clear message + exit 0.
- **Live Ollama smoke (gated; skips without Ollama, never fails CI):** build a real index, export both tiers, `discover` with a real `nomic-embed-text` question-embed, assert ranked non-crash output. *(Run after the gemma4:12b ratification completes — Ollama has a single inference slot.)*

---

## 8. Reused APIs (call, do not re-create)

- `embeddings.EmbeddingStore.load(library_path) -> EmbeddingStore | None`; `.provenance` (`Provenance(model, dims, normalization, corpus_hash, schema_version)`); the underlying matrix/rows accessors.
- `embeddings.chunk_pages(library_path)` + `embeddings.corpus_hash(page_hash_pairs)` — freshness gate on export.
- `fusion.compatible(prov_a, prov_b) -> bool` — compatibility gate on discover (model+dims+normalization; corpus_hash excluded).
- `backends.fake_backend.FakeBackend` (`.embed`, `.embedding_model_id()`); `AnthropicBackend` omits `embedding_model_id`. Discover requires an **embedding-capable** backend: if `embedding_model_id` is absent (or `embed` is unavailable), `discover` fails fast with a clear stderr message and a non-zero exit — there is no fallback (unlike M3c-2, which has the M2b path to fall back to; discovery has nothing to fall back *to*).
- numpy (already an `[offline]` dep) for vectors + k-means.

---

## 9. File structure

| File | Change | Responsibility |
|---|---|---|
| `scripts/fingerprint.py` | **new** | `export_fingerprint`, `write_fingerprint`, `load_fingerprint`, `_kmeans`, `score_fingerprint`, `discover` + small typed result structures |
| `scripts/kb_offline_cli.py` | modify | `fingerprint export` + `discover` subcommands; `_cmd_fingerprint_export`, `_cmd_discover`; `fingerprints_override` test seam |
| `tests/test_kb_offline_fingerprint.py` | **new** | round-trip, privacy, tiers, integrity/compat, scoring/ranking |
| `tests/test_kb_offline_cli.py` | modify | export + discover CLI tests |
| `tests/test_kb_offline_ollama_smoke.py` | modify | gated live export-both-tiers + discover smoke |

---

## 10. Decisions log

1. **Full cross-org exchange (B), not local-only (A).** The vision is shareable fingerprints across orgs, not just ranking already-registered local libraries.
2. **Both tiers, publisher's choice per library.** Coarse (privacy-conservative) and page (precision-favoring); discovery handles a mixed received set.
3. **Tier coarse = K k-means centroids (+ weights), not a single centroid.** A single mean is useless for multi-topic libraries; centroids preserve topical coverage while hiding per-page geometry.
4. **Tier page = bag of page vectors with page_ids stripped.** The who-to-ask output never needs filenames; dropping them removes the biggest leak.
5. **Nested JSON float arrays, not base64.** Round-trip is lossless (float32→float64→float32 is exact + shortest-repr JSON); readability/auditability wins for a trust artifact; size cost acceptable.
6. **Raw score + tier label (option a), not calibrated bands (option b).** No labelled cross-org ground truth to calibrate cutoffs; v1 stays truthful with raw max-cosine + `--min-score`; bands deferred to a future discovery eval.
7. **`{handle, owner, contact}` who-to-ask payload.** No topic summaries (would leak), no less (handle-only is unhelpful).
8. **No `import` command in v1.** Receiving = dropping a `.kbfp.json` in a directory.
9. **Freshness gate on export, compatibility gate on discover.** Don't publish stale coverage; never score incomparable cross-model vectors.
