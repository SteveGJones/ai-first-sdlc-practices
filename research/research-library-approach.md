# The Research Library & Librarian Approach

**A reusable pattern for building evidence-based programme knowledge**

---

## What This Is

A three-layer architecture for building, maintaining, and querying a programme-specific research evidence base using AI-powered deep research engines and an AI librarian agent. The approach produces a structured, citable knowledge base that any team member or AI agent can query for evidence-backed decisions.

This was developed on the ODP programme (22 library files, 300+ findings, 200+ peer-reviewed citations) and is designed to be replicated on any programme where decisions need to be grounded in evidence rather than opinion.

---

## Why It Works

Most programme decisions are made on experience and instinct. That's fine for routine work, but for novel or high-stakes decisions — architecture choices, measurement design, transformation strategy, governance models — you want to know what the research actually says.

The problem is that research is scattered across academic journals, industry reports, vendor whitepapers, and practitioner books. Nobody has time to read it all, and even if they did, the findings are hard to retrieve six months later when you need them in a stakeholder meeting.

This approach solves three problems:

1. **Research is expensive to do but cheap to store.** Deep research engines (Perplexity Pro, Gemini Deep Research, ChatGPT Deep Research) can synthesise hundreds of sources in minutes. The investment is in designing good prompts, not in reading papers.

2. **Findings decay without structure.** Raw research results are long, unindexed, and hard to search. The library layer compresses raw results into structured, tagged, cross-referenced files that an AI agent can search in seconds.

3. **Knowledge leaves with people.** A structured library with a librarian agent means the evidence base survives team changes. Any new team member (human or AI) can query the library and get citable evidence immediately.

---

## The Architecture

```
Layer 1: RESEARCH PROMPTS          Layer 2: LIBRARY FILES           Layer 3: LIBRARIAN AGENT
(generate the evidence)            (structure the evidence)         (retrieve the evidence)

+-------------------+              +-------------------+            +-------------------+
| 19 structured     |  Deep        | 22 synthesised    |  Shelf    | AI agent with     |
| research prompts  | ------>      | library files     | ------>   | pre-computed      |
| (engine-agnostic) |  Research    | (YAML + markdown) |  Index    | shelf index       |
+-------------------+  Engines     +-------------------+            +-------------------+
                                          |                                |
                                          v                                v
                                   +-------------------+            +-------------------+
                                   | Master index      |            | Structured        |
                                   | (_index.md)       |            | evidence blocks   |
                                   | 4 lookup tables   |            | with citations    |
                                   +-------------------+            +-------------------+
                                          |
                                          v
                                   +-------------------+
                                   | Raw results       |
                                   | (preserved for    |
                                   | deep reference)   |
                                   +-------------------+
```

Each layer serves a different purpose and a different audience:

| Layer | Purpose | Audience | Shelf life |
|-------|---------|----------|------------|
| Research Prompts | Generate evidence | Deep research engines | Reusable across engines |
| Library Files | Structure and cross-reference evidence | AI agents, architects, reviewers | Updated as new research arrives |
| Shelf Index | Fast file selection for the librarian | Librarian agent only | Regenerated when library changes |
| Master Index | Human-friendly multi-dimensional lookup | Programme team | Updated with library |
| Raw Results | Preserve full unabridged research | Deep reference only | Archived, not edited |
| Librarian Agent | Retrieve and synthesise on demand | Anyone who needs evidence | Stateless — reads library each time |

---

## Layer 1: Research Prompts

### What They Are

Structured research commissions designed for deep research engines. Each prompt is a standalone brief that can be pasted into Perplexity Pro, Gemini Deep Research, ChatGPT Deep Research, or used to guide manual academic searches.

### Prompt Structure

Every prompt follows the same template:

```markdown
# Deep Research: [Topic]

## Research Question
[One clear question — what are we trying to answer?]

## Why This Matters
[2-3 sentences — the hypothesis we're testing and why the answer matters
to the programme. No confidential information.]

## Investigation Structure

### Layer 1: [The Problem]
[Questions that establish the scale and nature of the problem.
Specific guidance on what to search for, which studies to look for,
what data points matter.]

### Layer 2: [Current Solutions]
[Questions about existing frameworks, tools, methodologies.
Specific names to search for.]

### Layer 3: [What Works]
[Questions about evidence for effectiveness.
Specific metrics and outcomes to look for.]

### Layer 4: [How to Implement]
[Questions about practical implementation.
Calibration, weighting, failure modes.]

### Layer 5: [Real-World Evidence]
[Questions about case studies and outcomes.
Named organisations, measured results.]

## Source Priority
1. Peer-reviewed academic studies
2. Large-scale industry research
3. Named case studies with measurable outcomes
4. Practitioner books with empirical backing
5. Tool vendor research (acknowledged bias)

## What Would Change Our Thinking
[Intellectual honesty — what disconfirming evidence looks like.
This forces the research engine to look for contradictions.]

## Deliverable Expected
[What a useful answer looks like — structured synthesis, not just a list.]
```

### Design Principles

**Be specific, not broad.** "What predicts project failure?" produces generic results. "What financial metrics predict margin erosion in IT services delivery, and at what thresholds do they become reliable?" produces actionable evidence with specific numbers.

**Name what you're looking for.** Don't just ask "what frameworks exist?" — name the ones you know about (DORA, SPACE, EVM) and ask the engine to find ones you don't know about. This anchors the search while leaving room for discovery.

**Include disconfirming evidence.** The "What Would Change Our Thinking" section is critical. It forces the research engine to search for evidence against your hypothesis, not just for it. This produces a more honest evidence base.

**Keep them confidential-information-free.** Prompts should contain zero organisation names, system names, internal processes, or proprietary concepts. This makes them safe to paste into any public research tool and reusable across projects.

**Layer the investigation.** 5-6 layers of progressively deeper inquiry produce better results than a single flat question. Each layer builds on the previous one, guiding the engine from problem definition through to practical implementation.

### Batching Strategy

Group prompts by theme so findings from one batch inform the next:

| Batch | Focus | Prompts | Why This Order |
|-------|-------|---------|----------------|
| 1 | Measurement foundations | What to measure, which frameworks exist | Establishes vocabulary |
| 2 | Predictive signals | What actually predicts outcomes | Identifies which measurements matter |
| 3 | Organisational design | How organisations handle visibility and gaming | Addresses the human side |
| 4 | Deep dives | Extend earlier prompts with targeted follow-up | Fill gaps found in batches 1-3 |
| 5 | Transformation | How to implement change successfully | Uses all prior evidence |

### Running Prompts Across Multiple Engines

Run the same prompt in 2-3 engines and compare:
- **Convergence** indicates strong evidence (multiple engines find the same studies)
- **Divergence** indicates contested territory (worth investigating further)
- **Unique finds** in one engine suggest it accessed sources the others missed

---

## Layer 2: Library Files

### What They Are

Synthesised, structured research files — one per topic. Each file compresses 5,000-15,000 words of raw research into a 1,500-3,000 word structured synthesis with tagged frontmatter, numbered findings, actionable thresholds, and full citations.

### File Structure

Every library file follows the same format:

```markdown
---
title: "[Topic]"
domain: [comma-separated topic tags]
status: active
tags: [array of search terms]
source: [path to raw research result]
cross_references:
  - library/related-file-1.md
  - library/related-file-2.md
---

## Key Question
[The research question this file answers — one sentence]

## Core Findings
[Numbered list. Each finding is one bullet point with:
  - A specific claim
  - A specific number or data point
  - A citation (author, year, sample size/methodology, publication)]

## Frameworks Reviewed
[Table comparing relevant frameworks, their evidence base, and limitations]

## Actionable Thresholds
[Table of specific numbers you can use in design:
  Metric | Threshold | Source | Signal]

## Design Principles
[What the research says about how to build things, not just what to measure]

## Key References
[Full citations for the primary sources — 10-20 references per file]

## Programme Relevance
[How this maps to specific programme artifacts, issues, and decisions.
This section is programme-specific; everything above is reusable.]
```

### Synthesis Rules

When creating library files from raw research results:

1. **Every finding must have a citation.** No unsourced claims. If the raw result doesn't cite a source, don't include the finding.
2. **Prefer large-N studies.** A finding from 16,000 projects (Flyvbjerg) is stronger than one from 12 projects. Note sample sizes.
3. **Note methodology.** "Self-report survey" is weaker than "system telemetry analysis." "RCT" is stronger than "observational study."
4. **Include contradictions.** If two studies disagree, report both with their methodologies. Let the reader judge.
5. **Extract thresholds.** The most valuable output is specific numbers — "TCPI >1.10 = unrecoverable" is more useful than "TCPI is an important metric."
6. **Cross-reference aggressively.** Every file should link to 2-4 related files. Findings that converge across multiple files are flagged as stronger evidence.

### Extending Library Files

As new research arrives (new prompts, new batches, updated studies), append to existing files rather than creating new ones:

```markdown
## Deep Research Additions (Batch N)

[New findings following the same numbered format,
clearly marked as additions so the original synthesis is preserved]
```

This maintains a single authoritative file per topic while preserving the provenance of when findings were added.

---

## Layer 2.5: The Indexes

Two index files serve different purposes.

### Master Index (`_index.md`)

A human-readable lookup with four dimensions:

1. **By Question** — "If you need to know X, start here" table mapping natural-language questions to library files
2. **By Artifact** — "When building X, read these" table mapping programme deliverables to relevant research
3. **By Issue** — Table mapping known programme issues to relevant evidence
4. **Full Catalogue** — Complete list of all files with topic, key numbers, and source

The master index is the entry point for humans browsing the library. It answers: "I'm working on X, which files should I read?"

### Shelf Index (`_shelf-index.md`)

A compact machine-readable index (~150 lines for 22 files) designed for the librarian agent. For each file:

```markdown
## N. filename.md
**Terms:** [20-30 keywords for matching against queries]
**Facts:** [3-5 headline statistics with citations — the top findings]
**Links:** [Programme-specific links: issues, measurements, personas, artifacts]
```

The shelf index is the librarian's first step — it reads this every time, identifies the 2-4 most relevant files, then deep-reads only those files. This keeps retrieval fast even as the library grows.

**Key design point:** The shelf index must be regenerated whenever the library changes. It's a derived artifact, not a source of truth.

---

## Layer 3: The Librarian Agent

### What It Is

An AI agent (defined as a system prompt) that searches the library and returns structured evidence. It does two things:

1. **Retrieve** — Find specific statistics, thresholds, and citations
2. **Synthesise** — Connect findings across multiple files to build evidence-based arguments

### How It Works

```
Query received
     |
     v
Read shelf index (ALWAYS first)
     |
     v
Match query against Terms, Facts, Links
     |
     v
Identify 2-4 most relevant files
     |
     v
Deep-read those files in full
     |
     v
Return structured evidence
```

### Output Formats

For **retrieval queries** ("What does the research say about X?"):

```markdown
### [Topic]

**Finding**: [Specific claim or statistic]
**Source**: [Citation — author, year, sample size/methodology]
**Threshold**: [Quantified value if applicable]
**Library file**: [filename.md]
**Programme link**: [How this applies — 1 sentence]
```

For **synthesis queries** ("Build me the case for X"):

```markdown
### [Argument Title]

**Claim**: [The synthesised conclusion]

**Supporting evidence**:
1. [Finding from file A] — [citation]
2. [Finding from file B] — [citation]
3. [Finding from file C] — [citation]

**Caveats**: [Contradictions, limitations, gaps]

**Programme application**: [How this applies specifically]
```

### Agent Design Principles

**Model selection matters.** The librarian is a retrieval-and-synthesis task, not a creative task. A fast, cheaper model (Sonnet-class) works well because the intelligence is in the library, not the agent. Save the expensive model for architecture and design decisions.

**Stateless by design.** The librarian reads the shelf index fresh every time. No memory, no state. This means the library can be updated and the librarian immediately reflects the changes.

**Honest about gaps.** The librarian must say "the library has no evidence on this" rather than guessing. This is critical for trust — if users learn the librarian sometimes invents citations, they'll stop trusting it entirely.

**Synthesis rules are explicit.** When connecting findings across files:
- Label which finding comes from which file
- Only synthesise when the connection is defensible
- Flag inferences vs direct findings
- Report contradictions honestly
- Never invent statistics or citations

**Boundary with other agents.** The librarian retrieves evidence. It does not make architecture decisions, provide change management advice, or recommend implementation approaches. Those are separate agent roles that _consume_ the librarian's output.

---

## How to Replicate on a New Programme

### Step 1: Identify Your Research Questions (1-2 days)

Start with the programme's key decisions and work backwards:

- What are the 5-10 most important design decisions the programme needs to make?
- What assumptions is the programme making that could be wrong?
- Where are stakeholders disagreeing? (Research can break deadlocks)
- What does the programme not know that it needs to know?

Write one research prompt per question using the template above. Aim for 10-20 prompts. Quality matters more than quantity — a well-structured prompt produces 10x better results than a vague one.

### Step 2: Run the Research (1-2 days)

Run each prompt through 1-2 deep research engines. Save the raw results in a `research/deep-research-results/` directory. Don't edit them — they're your source of truth.

Budget approximately 10-15 minutes per prompt (engine processing time + quick review of results).

### Step 3: Synthesise into Library Files (2-3 days)

For each raw result, create a structured library file following the template. This is the most time-intensive step but also the most valuable — you're compressing and structuring the knowledge for reuse.

Tips:
- One file per topic, not per prompt (some prompts may feed into the same file)
- Extract every specific number, threshold, and citation
- Cross-reference aggressively between files
- Write the "Programme Relevance" section last — it connects the general evidence to your specific context

### Step 4: Build the Indexes (half day)

Create the master index with 3-4 lookup dimensions relevant to your programme. Create the shelf index with terms, facts, and links for each file.

### Step 5: Define the Librarian Agent (half day)

Write the agent system prompt following the pattern above. Key customisations:
- File paths for your library location
- Query routing examples relevant to your programme
- Boundary definitions (what the librarian does and doesn't do)
- Shelf index path

### Step 6: Use It

The library is now queryable. As the programme progresses:
- New questions arise — write new prompts, run them, add to the library
- Findings get challenged — update files with new evidence
- The shelf index gets regenerated when files change
- The librarian agent doesn't need updating (it's stateless)

### Timeline

| Step | Effort | Output |
|------|--------|--------|
| Research questions | 1-2 days | 10-20 structured prompts |
| Run research | 1-2 days | Raw results (50,000-150,000 words) |
| Synthesise library | 2-3 days | 10-20 library files (30,000-60,000 words) |
| Build indexes | 0.5 day | Master index + shelf index |
| Define librarian | 0.5 day | Agent system prompt |
| **Total** | **5-8 days** | **Evidence base for the programme** |

---

## What We Learned

### Things that worked well

**Deep research engines are remarkably good at academic synthesis.** Perplexity Pro in particular consistently found relevant peer-reviewed studies with correct citations. Running the same prompt across 2-3 engines and looking for convergence produced a highly reliable evidence base.

**The shelf index transformed retrieval speed.** Without it, the librarian had to scan all 22 files. With a 150-line compact index, it identifies the right 2-4 files in seconds. This is the difference between a useful tool and a slow one.

**Structured prompts produce structured results.** The 5-layer investigation structure in each prompt meant the research engines returned organised, layered evidence rather than flat lists. The prompts did half the synthesis work.

**"What Would Change Our Thinking" produced the best findings.** Asking the engine to look for disconfirming evidence consistently surfaced the most interesting and useful results — contradictions, caveats, and boundary conditions that shaped better design decisions.

**The library became an asset beyond its original purpose.** It was built for architecture design but proved equally valuable for stakeholder communications, executive reports, transformation planning, and expert reviews. Citable evidence with specific numbers changes the quality of every conversation.

### Things to watch for

**Citation accuracy needs verification.** Deep research engines occasionally hallucinate citations or attribute findings to the wrong author. Spot-check 10-20% of citations against the original sources, especially for high-stakes claims.

**Library files drift if not maintained.** When new findings arrive, they must be integrated into existing files (not just appended). Periodically review each file for internal consistency.

**The librarian is only as good as the library.** If a topic isn't covered, the librarian should say so — but teams often forget this and treat the librarian as omniscient. Set expectations that the library covers specific topics, not everything.

**Programme Relevance sections need updating.** As the programme evolves, the mapping from general evidence to programme-specific context changes. These sections are the most maintenance-intensive part of the library.

---

## File Structure Reference

```
project/
  library/
    _index.md                    # Master index (4 lookup dimensions)
    _shelf-index.md              # Compact machine index for librarian
    delivery-health-scoring.md   # Library file (one per topic)
    financial-early-warning.md
    information-asymmetry.md
    ... (10-20 files)
  research/
    deep-research-prompts/
      00-index.md                # Prompt catalogue
      01-topic-one.md            # Structured research prompt
      02-topic-two.md
      ...
    deep-research-results/
      result-01-topic-one.md     # Raw, unedited engine output
      result-02-topic-two.md
      ...
  .claude/agents/                # Or equivalent agent config location
    research-librarian.md        # Librarian agent system prompt
```

---

## Numbers from ODP (for reference)

| Metric | Value |
|--------|-------|
| Research prompts written | 19 |
| Library files produced | 22 |
| Unique findings extracted | 300+ |
| Peer-reviewed citations | 200+ |
| Raw research words | ~150,000 |
| Synthesised library words | ~50,000 |
| Shelf index size | ~150 lines |
| Time to build (estimated) | ~6 days |
| Times queried in first week | 50+ (across 6 expert reviews, executive report, transformation planning) |

---

*This document describes the Research Library & Librarian approach developed on the ODP programme (Capgemini I&D, 2026). The approach is programme-agnostic and designed for reuse.*
