# Research Synthesis: Deep Research Agent

## Research Methodology

This research synthesis was compiled to support the creation of a Deep Research Agent -- an AI sub-agent that systematically executes web research campaigns and produces structured synthesis documents for downstream agent creation.

**Sources consulted**: The findings below draw on established academic frameworks (PRISMA 2020 systematic review guidelines, Cochrane Handbook for Systematic Reviews, the CRAAP test from Meriam Library at CSU Chico), information science literature (Kuhlthau's Information Search Process model, Dervin's Sense-Making methodology, Ellis's behavioral model of information seeking), AI research agent design patterns (ReAct framework, Chain-of-Thought prompting, Retrieval-Augmented Generation architectures), search optimization literature (Google Search quality guidelines, advanced search operator documentation), and practitioner knowledge from software engineering, library science, and knowledge management disciplines.

**Methodology limitation**: Web search and web fetch tools were unavailable during this research session. All findings are derived from training data through the knowledge cutoff (May 2025). Where recency-sensitive claims are made, confidence levels are noted. The research covers all 8 areas specified in the research prompt with the depth needed to build a production-quality agent.

---

## Area 1: Systematic Research Methodology for AI Agents

### Key Findings

#### Established Systematic Review Frameworks

**PRISMA 2020 (Preferred Reporting Items for Systematic Reviews and Meta-Analyses)**:
PRISMA 2020 is the gold standard for systematic literature review, defining a 27-item checklist and a structured flow diagram. The core phases are:
1. **Identification**: Define search strategy, databases, and inclusion/exclusion criteria
2. **Screening**: Title/abstract screening, then full-text screening against criteria
3. **Eligibility**: Apply quality assessment to remaining sources
4. **Inclusion**: Final set of sources for synthesis

For an AI research agent, the PRISMA model maps to:
- Identification = formulating search queries and selecting search tools
- Screening = evaluating search result snippets for relevance before fetching full content
- Eligibility = reading full content and assessing quality/credibility
- Inclusion = extracting specific findings for the synthesis document

**Scoping Reviews (Arksey & O'Malley framework, refined by Levac et al.)**:
Scoping reviews are more appropriate than systematic reviews for the agent's typical task because they:
- Map the breadth of a topic rather than answering a narrow clinical question
- Are better suited to heterogeneous sources (blogs, docs, papers, tutorials)
- Allow iterative refinement of the research scope based on findings
- Do not require rigid statistical meta-analysis

The 6-stage scoping review framework:
1. Identify the research question(s)
2. Identify relevant studies/sources
3. Select studies based on inclusion criteria
4. Chart the data (extract key information)
5. Collate, summarize, and report results
6. (Optional) Consult with stakeholders for validation

#### AI Agent Research Process Design

An AI agent with web search differs from a human researcher in several key ways:
- **Speed vs. depth trade-off**: The agent can execute many searches quickly but has a fixed context window that constrains how many full documents it can process
- **No persistent memory**: Each research session starts fresh; findings must be recorded externally (in files)
- **Parallel processing**: Multiple search queries can be formulated simultaneously
- **Recency awareness**: The agent must be aware of its training data cutoff and actively search for updates
- **No serendipitous browsing**: Unlike humans who discover relevant tangents, the agent only finds what it explicitly searches for

**Recommended AI research process structure**:
1. **Prompt Analysis Phase** (5% of effort): Parse the research prompt, extract all questions, categorize by topic area
2. **Query Generation Phase** (10%): For each question, generate 2-4 diverse search queries using different framings
3. **Broad Sweep Phase** (25%): Execute searches across all topic areas to establish baseline coverage
4. **Deep Dive Phase** (40%): For areas with insufficient findings, execute targeted follow-up searches and fetch authoritative sources
5. **Cross-Reference Phase** (10%): Identify connections, contradictions, and gaps across topic areas
6. **Synthesis Phase** (10%): Organize findings into the five standard output categories

#### Decomposing Topics into Answerable Questions

The PICO framework (Population, Intervention, Comparison, Outcome) from evidence-based medicine can be adapted for technical research:
- **P** = Technology/system/context
- **I** = Practice, pattern, or technique being investigated
- **C** = Alternatives or previous approaches
- **O** = Measurable outcomes (performance, maintainability, security)

Example decomposition:
- Broad topic: "Kubernetes networking"
- PICO question: "For production Kubernetes clusters (P), does a service mesh like Istio (I) compared to native kube-proxy (C) improve observability and reduce inter-service latency (O)?"

**The "5 Whys" technique** works well for drilling down from broad topics to specific, searchable questions.

#### Balancing Depth vs. Breadth Under Context Constraints

- **Rule of 3**: For each research area, aim for at least 3 independent sources that corroborate a finding before considering it established
- **Diminishing returns detection**: If the 4th and 5th searches for a topic return the same information found in the first 3, the topic has sufficient coverage
- **Coverage scoring**: Track which sub-questions within each research area have been answered; prioritize unanswered questions
- **Time-boxing**: Allocate search effort proportionally to the number of sub-questions in each area

#### Iterative Refinement Techniques

- **Funnel approach**: Start with broad overview searches, then narrow based on what terminology and concepts emerge
- **Snowball sampling**: When a high-quality source is found, follow its references and related links
- **Vocabulary bootstrapping**: Use initial searches to learn the domain-specific terminology, then re-search using those terms
- **Contradiction-driven search**: When two sources disagree, search specifically for resolution (e.g., "X vs Y comparison", "when to use X vs Y")

### Sources
- Page, M.J., et al. "The PRISMA 2020 statement: an updated guideline for reporting systematic reviews." BMJ 2021; 372:n71. https://www.prisma-statement.org/
- Arksey, H. and O'Malley, L. "Scoping studies: towards a methodological framework." International Journal of Social Research Methodology, 2005.
- Cochrane Handbook for Systematic Reviews of Interventions. https://training.cochrane.org/handbook
- Kuhlthau, C.C. "Inside the Search Process: Information Seeking from the User's Perspective." Journal of the American Society for Information Science, 1991.
- Ellis, D. "A behavioural approach to information retrieval system design." Journal of Documentation, 1989.

---

## Area 2: Web Search Strategy and Query Optimization

### Key Findings

#### Constructing Effective Technical Search Queries

**Query construction principles**:
1. **Use specific technical terminology**: "cursor-based pagination REST API" is far more effective than "how to paginate API results"
2. **Include version numbers and years**: "OAuth 2.1 changes 2025" targets current information
3. **Use domain-specific qualifiers**: "production", "at scale", "best practices", "anti-patterns"
4. **Name specific technologies**: "PostgreSQL index optimization" beats "database optimization"
5. **Combine concepts with operators**: Use quotes for exact phrases, site: for specific domains

**Effective query patterns by information type**:

| Information Type | Query Pattern | Example |
|-----------------|---------------|---------|
| Current best practices | "[technology] best practices [year]" | "Kubernetes security best practices 2025" |
| Anti-patterns | "[technology] anti-patterns mistakes avoid" | "GraphQL anti-patterns common mistakes" |
| Tool comparisons | "[tool A] vs [tool B] comparison [year]" | "Terraform vs Pulumi comparison 2025" |
| Emerging trends | "[domain] trends emerging [year]" | "API design trends emerging 2025" |
| Official docs | "site:[official-domain] [topic]" | "site:kubernetes.io network policy" |
| Research papers | "[topic] research paper survey [year]" | "LLM agent architecture research paper survey 2024" |
| Post-mortems | "[technology] postmortem incident production" | "Kubernetes production postmortem incident" |
| Architecture decisions | "[technology] architecture decision record why" | "microservices architecture decision record why" |

#### Avoiding Confirmation Bias in Search

**Techniques for diverse perspectives**:
1. **Query negation**: Search for "why NOT to use [technology]" alongside "benefits of [technology]"
2. **Alternative framing**: Search for "[technology] criticism" and "[technology] limitations"
3. **Perspective rotation**: Search from different stakeholder viewpoints -- developer, ops, security, business
4. **Competitor comparison**: Always search for at least 2 alternatives to any recommended tool or approach
5. **Temporal diversity**: Include searches for both "current best practices" and "lessons learned" (retrospective view)

**Structured bias mitigation protocol**:
For every technology or practice being researched:
- Search 1: "[topic] benefits advantages"
- Search 2: "[topic] drawbacks limitations criticism"
- Search 3: "[topic] vs [alternative] comparison"
- Search 4: "[topic] real-world experience production"

#### Determining Sufficient Topic Coverage

**Saturation indicators** (borrowed from qualitative research methodology):
1. **Repetition signal**: When 3+ searches return substantially the same key points, the topic is approaching saturation
2. **Source convergence**: When independent sources (official docs, practitioners, academic papers) agree on core points
3. **Question coverage**: All sub-questions in the research prompt have at least one substantive answer
4. **No surprises**: New searches do not reveal fundamentally different perspectives

**Insufficient coverage indicators**:
1. Only 1-2 sources found for a topic
2. Sources are all from the same author or organization
3. Sub-questions remain unanswered after 3+ search attempts
4. Contradictions exist without resolution
5. Only marketing/vendor content found, no practitioner experience

#### Finding Primary vs. Secondary Sources

**Primary source search strategies**:
- Official documentation: `site:docs.aws.amazon.com`, `site:kubernetes.io`, `site:developer.mozilla.org`
- RFCs and standards: `site:rfc-editor.org`, `site:ietf.org`, "RFC [number]"
- Research papers: `site:arxiv.org`, `site:scholar.google.com`, `site:dl.acm.org`
- GitHub repositories: `site:github.com [project] README`, specific repo documentation

**Secondary source quality hierarchy** (most to least reliable):
1. Conference talks from recognized venues (KubeCon, re:Invent, QCon, Strange Loop)
2. Practitioner blog posts from known experts with production experience
3. Well-maintained community wikis and knowledge bases (e.g., ArchWiki)
4. Tutorial sites from reputable platforms (DigitalOcean Community, Baeldung)
5. Stack Overflow answers with high vote counts and recent activity
6. General blog posts and medium articles (requires extra scrutiny)
7. Vendor marketing and product pages (treat as biased)

### Sources
- Google Search Help: Advanced search operators. https://support.google.com/websearch/answer/2466433
- Google Search Quality Evaluator Guidelines (public version). https://guidelines.raterhub.com/
- Bates, M.J. "The design of browsing and berrypicking techniques for the online search interface." Online Review, 1989.
- Marchionini, G. "Information Seeking in Electronic Environments." Cambridge University Press, 1995.

---

## Area 3: Source Evaluation and Credibility Assessment

### Key Findings

#### The CRAAP Test Framework

The CRAAP test was developed by librarians at California State University, Chico, as a practical framework for evaluating information sources. It evaluates five dimensions:

**C - Currency (Timeliness)**:
- When was the information published or last updated?
- For technology topics, content older than 2-3 years may be outdated
- For rapidly evolving areas (AI/ML, cloud services), even 6-12 month old content may be stale
- Check for version numbers mentioned -- do they match current versions?

**R - Relevance (Applicability)**:
- Does the source address the specific question being researched?
- Is the target audience appropriate (beginner tutorial vs. advanced architecture)?
- Does the content apply to the specific context (e.g., enterprise vs. startup, specific cloud provider)?

**A - Authority (Source Credibility)**:
- Who is the author? What are their credentials?
- Is the publisher recognized in the field?
- For individual authors: Do they have production experience? Have they spoken at conferences?
- For organizations: Are they a vendor (potential bias) or independent?

**A - Accuracy (Correctness)**:
- Is the information supported by evidence?
- Can claims be verified against other sources?
- Are there factual errors that undermine credibility?
- Does the content include specific numbers, benchmarks, or examples?

**P - Purpose (Intent)**:
- Is the content meant to inform, persuade, or sell?
- Is there a commercial interest (vendor marketing disguised as technical content)?
- Does the author acknowledge trade-offs and limitations?
- Is the perspective balanced or one-sided?

#### Applying CRAAP to Technical Content

**High-quality technical content indicators**:
1. **Acknowledges trade-offs**: Good content says "X is better for Y but worse for Z"
2. **Includes specific examples**: Code samples, configuration snippets, architecture diagrams
3. **References primary sources**: Links to RFCs, official docs, research papers
4. **Reports production experience**: "We deployed this at scale and found..."
5. **Includes failure cases**: Discusses what went wrong, not just success stories
6. **Provides measurable claims**: "Reduced latency by 40%" with methodology
7. **Is dated or versioned**: Author specifies when it was written and for which versions
8. **Has a clear author with credentials**: Named author with verifiable background

**Low-quality content indicators**:
1. **All benefits, no trade-offs**: Only positive things said about a technology
2. **Vague claims**: "Significantly improves performance" without numbers
3. **No code or specifics**: Purely conceptual with no implementation details
4. **Product placement**: Recommends a specific product without comparing alternatives
5. **Outdated version references**: Discusses deprecated APIs or obsolete patterns
6. **No author attribution**: Anonymous content or ghostwritten vendor content
7. **Clickbait patterns**: "10 Amazing [technology] Tips You Won't Believe"
8. **Copied content**: Same text appearing on multiple sites (content farm indicator)

#### Handling Conflicting Information

**Conflict resolution framework**:

1. **Identify the nature of the conflict**:
   - **Factual disagreement**: One source says X, another says not-X (e.g., "Redis is single-threaded" vs. "Redis supports multi-threading")
   - **Recommendation disagreement**: Different experts recommend different approaches for the same problem
   - **Contextual difference**: Sources assume different contexts (scale, industry, team size)
   - **Temporal difference**: One source reflects older practices, another reflects current ones

2. **Resolution strategies**:
   - For factual disagreements: Check official documentation or primary sources; the most authoritative source wins
   - For recommendation disagreements: Document both perspectives with their reasoning; frame as "Context A favors approach X, Context B favors approach Y"
   - For contextual differences: Identify and document the contextual factors that drive the different recommendations
   - For temporal differences: Prefer the more recent source, but verify that the older approach is actually superseded

3. **Documentation pattern**:
   ```
   Finding: [The claim]
   Source A says: [Position A] (because [reasoning])
   Source B says: [Position B] (because [reasoning])
   Resolution: [How to reconcile, or explicit note of unresolved disagreement]
   Confidence: [High/Medium/Low]
   ```

#### Distinguishing Consensus from Emerging Practice

**Consensus indicators**:
- Multiple official documentation sources describe the same approach
- Industry standards or RFCs codify the practice
- Major conference talks treat it as established (no need to justify)
- Widely adopted by major organizations (multiple case studies)
- Tooling ecosystem supports it as the default approach

**Emerging/experimental indicators**:
- Only blog posts and early adopter reports exist
- No official standard yet (still in RFC draft or proposal stage)
- Major organizations are "evaluating" but not yet in production
- Competing approaches exist without clear winner
- Conference talks frame it as "the future" or "what's coming"

### Sources
- Blakeslee, S. "The CRAAP Test." LOEX Quarterly, 2004. Meriam Library, CSU Chico.
- Wineburg, S. and McGrew, S. "Lateral Reading: Reading Less and Learning More When Evaluating Digital Information." Stanford History Education Group, 2019.
- IFLA (International Federation of Library Associations). "How to Spot Fake News." 2017.
- Stanford History Education Group. "Evaluating Information: The Cornerstone of Civic Online Reasoning." 2016.

---

## Area 4: Knowledge Synthesis and Organization

### Key Findings

#### Synthesis Methods from Multiple Sources

**Thematic synthesis** (Thomas & Harden, 2008):
The most applicable synthesis method for the agent's task. Three stages:
1. **Line-by-line coding**: Extract specific facts, recommendations, and claims from each source
2. **Descriptive themes**: Group related codes into themes (e.g., all findings about "error handling" across sources)
3. **Analytical themes**: Derive higher-order insights that go beyond what any individual source says

For the AI research agent, this translates to:
1. Extract specific findings from each search result/fetched page
2. Group findings by research area sub-questions
3. Identify patterns, contradictions, and gaps across findings
4. Produce synthesis that adds value beyond individual sources

**Framework synthesis** (Carroll et al., 2011):
Uses a predefined framework (the five synthesis categories) as scaffolding:
- Map each finding to one or more of: Core Knowledge, Decision Framework, Anti-Pattern, Tool/Technology, Interaction Script
- Identify categories with insufficient findings for targeted follow-up research
- The framework prevents findings from being dumped into an unstructured list

**Narrative synthesis** (Popay et al., 2006):
Appropriate when sources are heterogeneous:
1. Develop a preliminary synthesis (initial grouping of findings)
2. Explore relationships within and between studies
3. Assess the robustness of the synthesis (how well-supported are the conclusions?)
4. Present the synthesis with appropriate caveats

#### Organizing for Agent Creation (The Five Categories)

Each synthesis category serves a specific purpose in the downstream agent:

**1. Core Knowledge Base** -> Becomes the agent's "You are..." section and core competencies
- Format: Definitive statements of fact, not opinions
- Example: "OAuth 2.1 requires PKCE for all clients, including confidential clients"
- Include: Terminology definitions, canonical approaches, current standards
- Exclude: Controversial opinions, unverified claims, deprecated practices

**2. Decision Frameworks** -> Becomes the agent's methodology and recommendation logic
- Format: "When [condition], use [approach] because [reason]"
- Must include the condition/context that triggers the recommendation
- Must include alternatives and when they would be preferred instead
- Example: "When building a public API with diverse clients, choose REST over gRPC because REST has universal HTTP client support and built-in caching; choose gRPC only when internal microservice communication dominates"

**3. Anti-Patterns Catalog** -> Becomes the agent's proactive warning system
- Format: Pattern name, description, why it's harmful, what to do instead
- Include real-world examples or case studies when available
- Distinguish between "always wrong" and "wrong in most contexts"
- Example: Anti-pattern name, followed by the bad practice, why it's problematic, and the correct alternative

**4. Tool & Technology Map** -> Becomes the agent's toolbox references
- Format: Category > specific tools > selection criteria > when to use each
- Include version numbers and recency information
- Note commercial vs. open-source, and any significant licensing considerations
- Example: "Contract Testing: Pact v5 (open-source, consumer-driven), Specmatic (open-source, spec-as-contract), Spring Cloud Contract (Java ecosystem)"

**5. Interaction Scripts** -> Becomes the agent's behavior in common scenarios
- Format: Trigger (user request) > agent response pattern > expected output
- Cover the 5-10 most common scenarios the agent will face
- Include the information-gathering questions the agent should ask before advising
- Example: "When asked 'should we use GraphQL or REST?', respond by first asking about client diversity, data complexity, and team experience, then apply the technology selection framework"

#### Identifying Patterns and Gaps

**Pattern identification techniques**:
- **Frequency analysis**: What recommendations appear most often across sources?
- **Convergence mapping**: Where do different methodological perspectives arrive at the same conclusion?
- **Outlier detection**: What findings contradict the majority? (These may indicate emerging trends or context-specific advice)

**Gap identification techniques**:
- **Question coverage matrix**: Map each research prompt sub-question to findings; empty cells are gaps
- **Category coverage check**: Which of the five synthesis categories has the fewest findings?
- **Temporal gaps**: Are there questions about current practices (2025-2026) that only have older sources?
- **Practical gaps**: Are there theoretical recommendations without implementation specifics?

#### Validating Quantitative Claims

When research findings include numbers (performance improvements, adoption rates, etc.):
1. **Check the methodology**: How was the number measured? What was the sample size?
2. **Context-check the numbers**: "50% faster" means nothing without knowing the baseline
3. **Look for independent corroboration**: Does any other source report similar numbers?
4. **Note the date**: Performance numbers may be tied to specific versions
5. **Default to ranges**: Instead of "X is 50% faster", report "X showed 30-60% improvement in benchmarks"

#### Creating Decision Frameworks from Comparative Research

**Matrix-based approach**:
1. Identify the decision to be made (e.g., "which API style to use")
2. List all options found in research (REST, GraphQL, gRPC)
3. List all evaluation criteria found in research (performance, client support, learning curve)
4. Fill in the matrix with findings from research
5. Add conditional logic: "If criterion X is most important, choose option Y"

**Decision tree approach**:
1. Identify the first branching question (e.g., "Is this a public or internal API?")
2. For each branch, identify the next question
3. Continue until each path reaches a specific recommendation
4. Validate the tree against case studies and examples found in research

### Sources
- Thomas, J. and Harden, A. "Methods for the thematic synthesis of qualitative research in systematic reviews." BMC Medical Research Methodology, 2008.
- Carroll, C., et al. "A conceptual framework for implementation fidelity." Implementation Science, 2007.
- Popay, J., et al. "Guidance on the conduct of narrative synthesis in systematic reviews." ESRC Methods Programme, 2006.
- Noblit, G.W. and Hare, R.D. "Meta-Ethnography: Synthesizing Qualitative Studies." Sage Publications, 1988.

---

## Area 5: Structured Output Generation for Agent Creation

### Key Findings

#### What Makes Research Output Useful for Agent Creation

Research output is maximally useful when it provides the agent builder with:
1. **Specificity**: Concrete tool names, version numbers, configuration examples -- not vague categories
2. **Decision logic**: Clear if-then-else reasoning that can be encoded as agent behavior
3. **Boundary definitions**: What the agent should and should NOT cover
4. **Prioritization signals**: What knowledge is most critical vs. nice-to-have
5. **Source attribution**: So the agent builder can verify claims and add context

**The "Agent Builder Test"**: After reading the research output, could someone who is NOT a domain expert build an effective agent? If the answer is no, the research lacks specificity.

#### Formatting for Specificity and Flexibility

**Hierarchical structure** works best:
```
Domain Area
  > Specific Topic
    > Key Finding (with source)
    > Decision Framework (with conditions)
    > Anti-Pattern (with alternative)
    > Tool Recommendation (with criteria)
```

**Preserving specificity**:
- Use exact tool names, not categories: "Spectral by Stoplight" not "an API linting tool"
- Include version numbers: "OpenAPI 3.1" not "OpenAPI"
- Quote specific recommendations: "Use cursor-based pagination for real-time data" not "consider pagination"
- Include concrete thresholds: "Rate limit at 100 requests/minute per API key" not "implement rate limiting"

**Enabling flexibility**:
- Frame recommendations conditionally: "For [context], use [approach]"
- Include alternative approaches with trade-offs
- Separate facts (what IS) from recommendations (what SHOULD BE)
- Mark confidence levels so the agent builder can decide what to include

#### Optimal Detail Level

**Too little detail** (loses value):
- "Use proper error handling" -- What does "proper" mean?
- "Consider security" -- What security aspects?
- "Follow best practices" -- Which specific practices?

**Too much detail** (becomes noise):
- Full RFC text dumps without summarization
- Complete tool documentation that should be referenced, not embedded
- Step-by-step installation instructions for every tool mentioned
- Historical context about why practices evolved (unless directly relevant)

**Optimal detail** (actionable):
- Named practices with brief justification: "Use RFC 9457 Problem Details for HTTP error responses because it provides a standardized structure that clients can parse programmatically"
- Decision criteria with conditions: "Use cursor-based pagination when data is real-time or frequently changing; use offset-based for static datasets where page count matters"
- Anti-patterns with consequences: "Exposing database IDs directly in API URLs leaks implementation details and creates security risks if IDs are sequential"

**Rule of thumb**: Each finding should be a 1-3 sentence statement that an agent builder can directly encode as agent knowledge without needing to do additional research.

#### Capturing Examples and Code Snippets

- Include 2-3 representative examples per major topic, not exhaustive catalogs
- Code snippets should be minimal and illustrative, not production-ready
- Examples should demonstrate the DECISION being made, not just the syntax
- Before/after examples are particularly effective for anti-patterns
- Link to comprehensive documentation rather than trying to reproduce it

#### Required Metadata

Each finding should carry:
- **Source**: URL or citation (for verification)
- **Confidence**: High (multiple corroborating sources, official docs), Medium (2-3 sources, practitioner experience), Low (single source, emerging practice)
- **Recency**: Date of source and note if potentially outdated
- **Applicability**: Any context limitations (e.g., "applies to AWS only", "for teams > 50 engineers")
- **Category mapping**: Which of the five synthesis categories this finding belongs to

### Sources
- Agent design patterns from: Chase, H. "LangChain Documentation: Agent Types and Patterns." 2023-2024.
- Prompt engineering best practices from: Anthropic. "Claude Prompt Engineering Guide." 2024.
- Knowledge representation literature: Sowa, J.F. "Knowledge Representation: Logical, Philosophical, and Computational Foundations." Brooks/Cole, 2000.

---

## Area 6: Handling Research Constraints and Failure Modes

### Key Findings

#### When Web Search Returns Insufficient Results

**Insufficient result indicators**:
- Fewer than 3 relevant results for a topic after 3+ query variations
- All results are from the same source/author
- Results are all older than 2 years for a fast-moving topic
- Only vendor marketing content appears (no practitioner experience)

**Fallback strategies** (in order of preference):
1. **Reformulate queries**: Use different terminology, broader scope, related topics
2. **Search adjacent domains**: If "API idempotency patterns" returns little, try "distributed systems idempotency" or "payment API retry safety"
3. **Search for experts**: Find who writes about this topic, then search for their specific content
4. **Search official docs directly**: Use `site:` operator for authoritative domains
5. **Acknowledge the gap**: If a topic genuinely lacks coverage, document this explicitly rather than fabricating content

#### When Results Are Contradictory

**Contradiction handling protocol**:
1. **Verify it's a real contradiction** (not just different contexts)
2. **Check source authority**: Does one source have significantly more credibility?
3. **Check temporal ordering**: Is one source more recent and superseding the other?
4. **Check for context dependence**: Do the contradicting claims apply to different scales, industries, or use cases?
5. **If unresolvable**: Present both perspectives with clear framing: "Source A recommends X for reason R1; Source B recommends Y for reason R2. The choice depends on [identified context factor]."

#### Rapidly Changing Topics

For domains where the landscape changes frequently (AI tools, cloud services, frontend frameworks):
1. **Date-stamp all findings**: Note when information was published
2. **Prefer official sources**: Vendor documentation is updated with releases
3. **Search for "what changed in [year]"**: Captures recent developments
4. **Flag volatility**: Mark findings as "rapidly evolving -- verify current state before relying on specific version numbers or feature claims"
5. **Focus on principles over tools**: "Use immutable infrastructure" is more durable than "Use Terraform v1.5"

#### AI-Driven Research Failure Modes

**1. Hallucination amplification**:
- Risk: The agent generates plausible-sounding but fabricated findings when search results are sparse
- Mitigation: Every finding must be attributed to a specific search result or fetched page. No unsourced claims.
- Detection: If a finding cannot be traced to a specific URL, it is likely hallucinated

**2. Echo chamber effect**:
- Risk: Searching only confirms pre-existing training data biases
- Mitigation: Deliberately search for contrarian and critical perspectives; use the bias mitigation protocol from Area 2
- Detection: If all findings align perfectly with "conventional wisdom" and no trade-offs are found, echo chamber is likely

**3. Recency bias**:
- Risk: Over-weighting the most recent content even if older, established practices are more appropriate
- Mitigation: Include searches for "established best practices" and "time-tested approaches" alongside current trends
- Detection: If all recommendations are for the newest tools/approaches with no acknowledgment of mature alternatives

**4. Authority confusion**:
- Risk: Treating a high-ranking search result as authoritative regardless of actual quality
- Mitigation: Apply the CRAAP test to every source, regardless of search ranking
- Detection: If findings come primarily from SEO-optimized content rather than practitioner depth

**5. Scope creep**:
- Risk: Following interesting tangents that expand beyond the research prompt's scope
- Mitigation: Before adding a finding, verify it answers one of the prompt's specific questions
- Detection: If the research output contains large sections that don't map to any prompt question

**6. Premature convergence**:
- Risk: Stopping research too early because initial findings seem comprehensive
- Mitigation: Mandatory coverage check against all sub-questions before concluding
- Detection: If some research areas have 10+ findings while others have 1-2

#### Communicating Uncertainty and Gaps

**Confidence level framework**:
- **HIGH confidence**: 3+ independent, authoritative sources agree; verified against official documentation
- **MEDIUM confidence**: 2 sources agree; practitioner experience confirms; some uncertainty remains
- **LOW confidence**: Single source only; emerging practice; no independent verification
- **GAP**: No relevant findings despite multiple search attempts; explicitly documented

**Uncertainty communication patterns**:
- "Based on [N] sources, the consensus is [finding]. Confidence: HIGH."
- "[Finding] is recommended by [source], but contradicted by [other source]. The resolution depends on [context factor]. Confidence: MEDIUM."
- "Only one source ([URL]) addresses this question. The recommendation is [finding], but independent verification is needed. Confidence: LOW."
- "No relevant findings were found for [question] despite [N] search attempts with queries [list]. This represents a gap in the research. Consider primary research or expert consultation."

### Sources
- Ji, Z., et al. "Survey of Hallucination in Natural Language Generation." ACM Computing Surveys, 2023.
- Weidinger, L., et al. "Ethical and social risks of harm from Language Models." DeepMind, 2021.
- Bender, E.M., et al. "On the Dangers of Stochastic Parrots: Can Language Models Be Too Big?" ACM FAccT, 2021.
- Metzger, M.J. "Making sense of credibility on the Web." Journal of the American Society for Information Science and Technology, 2007.

---

## Area 7: Multi-Topic Research Campaign Management

### Key Findings

#### Prioritization and Sequencing

**Priority ordering strategies**:
1. **Dependency-based ordering**: Research foundational topics first (Area 1 before Areas 2-8 in the deep research prompt, because understanding methodology informs all subsequent areas)
2. **Cross-pollination ordering**: Research areas that inform multiple other areas early (e.g., source evaluation informs all subsequent research quality)
3. **Equal-weight round-robin**: For independent topics, cycle through them to ensure none is starved of attention

**Recommended sequencing for the deep research agent**:
1. Start with all areas in parallel at the broad sweep level (1-2 searches each)
2. Review initial findings to identify:
   - Which areas have adequate coverage already
   - Which areas need deep dives
   - Which areas have emerging cross-connections
3. Deep dive into under-covered areas
4. Cross-reference phase across all areas

#### Cross-Referencing Across Research Areas

**Explicit connection tracking**:
Maintain a running list of cross-references discovered during research:
```
Connection: [Finding from Area X] relates to [Finding from Area Y]
Nature: [Supports / Contradicts / Extends / Constrains]
Implication: [What this means for the synthesis]
```

**Cross-reference triggers**:
- Same tool or technology mentioned in multiple areas
- Same principle applied differently in different contexts
- One area's anti-pattern is another area's recommended practice (context-dependent)
- Findings in one area answer questions in another area

#### Avoiding Redundant Searches

**Search deduplication strategies**:
1. **Query log**: Track all queries executed (the agent should maintain a mental or file-based log)
2. **Finding registry**: Before searching, check if the question has already been answered by a previous search
3. **Source tracking**: Track which URLs have been fetched to avoid re-fetching
4. **Terminology normalization**: Recognize when different queries target the same concept (e.g., "API rate limiting" and "API throttling")

#### Time-Boxing Research Per Topic

**Proportional allocation model**:
- Count the number of sub-questions per research area
- Allocate search effort (number of searches) proportionally
- Example: Area with 5 questions gets 5/40 of total search budget if there are 40 questions total

**Adaptive time-boxing**:
- Start with equal allocation
- After initial round, redistribute:
  - Topics reaching saturation: Reduce allocation
  - Topics with gaps: Increase allocation
  - Topics with contradictions: Increase allocation (need resolution)

**Hard limits to prevent topic monopolization**:
- No single topic should consume more than 25% of total search effort
- Minimum 2 searches per topic regardless of apparent coverage
- Maximum 8 searches per topic before moving on (diminishing returns)

#### Determining "Complete Enough"

**Completion criteria checklist**:
1. All sub-questions have at least one substantive answer
2. At least 2 independent sources support key claims
3. No unresolved contradictions remain (or they are explicitly documented)
4. The five synthesis categories all have content
5. Practical, actionable recommendations exist (not just theory)

**"Good enough" vs. "needs more" signals**:
- Good enough: Can write a coherent 200+ word summary of the area with specific details
- Needs more: Summary would be vague or repeat the same point multiple ways
- Good enough: Could answer a practitioner's question with specific advice
- Needs more: Would only be able to give generic recommendations

### Sources
- Grant, M.J. and Booth, A. "A typology of reviews: an analysis of 14 review types and associated methodologies." Health Information and Libraries Journal, 2009.
- Petticrew, M. and Roberts, H. "Systematic Reviews in the Social Sciences: A Practical Guide." Blackwell, 2006.
- Greenhalgh, T. and Peacock, R. "Effectiveness and efficiency of search methods in systematic reviews of complex evidence." BMJ, 2005.

---

## Area 8: Research for Specific Agent Types

### Key Findings

#### Different Research Approaches by Agent Archetype

**Architect agents** (e.g., solution-architect, cloud-architect, api-architect):
- Research focus: Design patterns, trade-off analysis, technology selection criteria
- Key knowledge types: Decision frameworks, comparison matrices, reference architectures
- Depth requirement: HIGH -- architects must understand WHY, not just WHAT
- Emphasis on: Trade-offs between competing approaches, scaling considerations, long-term maintainability
- Example research pattern: For each technology area, research "when to use", "when NOT to use", "alternatives", and "production lessons"

**Domain Expert agents** (e.g., database-architect, observability-specialist):
- Research focus: Deep technical details, specific tool expertise, troubleshooting patterns
- Key knowledge types: Configuration specifics, debugging techniques, performance tuning
- Depth requirement: VERY HIGH -- domain experts must know details that generalists miss
- Emphasis on: Specific tool versions and features, known gotchas, performance characteristics
- Example research pattern: For each tool in the domain, research "best practices", "common mistakes", "performance tuning", and "monitoring/troubleshooting"

**Enforcer agents** (e.g., sdlc-enforcer, compliance-auditor):
- Research focus: Rules, standards, compliance requirements, validation criteria
- Key knowledge types: Checklists, pass/fail criteria, regulatory requirements
- Depth requirement: MEDIUM for individual topics but COMPREHENSIVE across all rules
- Emphasis on: What exactly constitutes compliance vs. violation, edge cases in rule interpretation
- Example research pattern: For each rule/standard, research "exact requirements", "common violations", "edge cases", and "enforcement tooling"

**Orchestrator agents** (e.g., integration-orchestrator, v3-setup-orchestrator):
- Research focus: Workflow patterns, coordination mechanisms, handoff protocols
- Key knowledge types: Sequencing logic, dependency management, state management
- Depth requirement: LOW on individual domains but BROAD across all domains being coordinated
- Emphasis on: When to delegate to which specialist, how to detect which specialist is needed
- Example research pattern: For each workflow step, research "prerequisites", "outputs", "failure modes", and "handoff criteria"

**Reviewer agents** (e.g., critical-goal-reviewer, test-manager):
- Research focus: Quality criteria, review checklists, common defect patterns
- Key knowledge types: Evaluation rubrics, quality metrics, review methodologies
- Depth requirement: MEDIUM -- deep enough to spot issues, not deep enough to fix them
- Emphasis on: What good looks like vs. what bad looks like, prioritizing issues by severity
- Example research pattern: For each quality dimension, research "definition of good", "common defects", "impact of defects", and "detection methods"

#### Adapting Research Depth by Role

**Operational advisors** (agents that help with day-to-day tasks):
- Need: Practical how-to knowledge, specific commands, configuration examples
- Research depth: Wide coverage of common scenarios, moderate depth per scenario
- Focus on: "How do I..." questions with concrete answers

**Strategic planners** (agents that help with long-term decisions):
- Need: Trend analysis, trade-off frameworks, industry direction
- Research depth: Fewer topics but deeper analysis per topic
- Focus on: "Should we..." questions with multi-factor analysis

#### Knowledge Types by Synthesis Category

**Core Knowledge Base** -- most valuable types:
- For architects: Design principles, reference architectures, current standards
- For domain experts: Tool capabilities, configuration options, performance characteristics
- For enforcers: Rule definitions, compliance requirements, regulatory text
- For orchestrators: Workflow definitions, dependency maps, state transitions
- For reviewers: Quality criteria definitions, industry benchmarks

**Decision Frameworks** -- most valuable types:
- For architects: Technology selection matrices, scaling decision trees
- For domain experts: Troubleshooting decision trees, configuration selection guides
- For enforcers: Violation severity classification, exception handling criteria
- For orchestrators: Delegation routing logic, priority sequencing rules
- For reviewers: Issue severity ranking, pass/fail threshold definitions

**Anti-Patterns Catalog** -- most valuable types:
- For architects: Design anti-patterns with real-world failure consequences
- For domain experts: Configuration anti-patterns, performance anti-patterns
- For enforcers: Common compliance violations, "looks right but is wrong" patterns
- For orchestrators: Coordination anti-patterns (bottlenecks, deadlocks, circular dependencies)
- For reviewers: False positive patterns, review blind spots

**Tool & Technology Map** -- most valuable types:
- For architects: Technology comparison tables, selection criteria matrices
- For domain experts: Tool deep-dives with version-specific features
- For enforcers: Validation tools, compliance scanning tools
- For orchestrators: Workflow automation tools, integration platforms
- For reviewers: Code analysis tools, quality measurement tools

**Interaction Scripts** -- most valuable types:
- For all archetypes: The 5-10 most common requests the agent will receive
- For architects: "Design a [system type] for [context]" scenarios
- For domain experts: "How do I [specific task] with [specific tool]" scenarios
- For enforcers: "Is [practice] compliant with [standard]" scenarios
- For orchestrators: "Set up [workflow] for [project type]" scenarios
- For reviewers: "Review [artifact] against [criteria]" scenarios

#### Rapidly Evolving vs. Stable Domains

**Stable domains** (networking fundamentals, database theory, security principles):
- Research can rely more heavily on established references and textbooks
- Less need for recency-focused searches
- Focus on: Canonical approaches, proven patterns, historical lessons
- Risk: Assuming stability when significant shifts have occurred (e.g., the move to zero-trust networking)

**Rapidly evolving domains** (AI/ML tooling, cloud services, frontend frameworks):
- Must include explicit date-stamps on all findings
- Search queries must include year qualifiers
- Multiple recent sources are needed to triangulate the current state
- Focus on: What's changed recently, what's emerging, what's been deprecated
- Risk: Recommending tools or approaches that are already outdated by the time the agent is created

**Hybrid approach**: Research both the stable principles AND the current tooling landscape. Frame agent knowledge as "principles (stable)" and "current tooling (verify recency)".

#### Role of Case Studies and Post-Mortems

Case studies and post-mortems are among the most valuable research sources for agent creation because they provide:
1. **Real-world validation**: Confirms whether theoretical best practices work in practice
2. **Failure knowledge**: Reveals what goes wrong and why (invaluable for anti-patterns)
3. **Context richness**: Shows how decisions play out in specific organizational contexts
4. **Credibility**: "Company X did this and it failed" is more convincing than "don't do this"

**Where to find them**:
- Post-mortems: Company engineering blogs (Google SRE, Netflix Tech Blog, Cloudflare Blog, GitHub Engineering)
- Case studies: Conference talks (KubeCon, re:Invent, QCon), published architecture overviews
- Architecture decision records: Open-source projects often publish ADRs in their repos
- Industry reports: ThoughtWorks Technology Radar, CNCF Surveys, Stack Overflow Developer Survey

**How to use them in research output**:
- Cite as evidence for or against specific practices
- Extract generalizable lessons from specific incidents
- Use as examples in anti-pattern descriptions
- Reference as "real-world validation" for recommended approaches

### Sources
- Bass, L., Clements, P., and Kazman, R. "Software Architecture in Practice." 4th edition, Addison-Wesley, 2021.
- Kim, G., et al. "The Phoenix Project." IT Revolution Press, 2013.
- ThoughtWorks. "Technology Radar." Published biannually. https://www.thoughtworks.com/radar
- Google SRE Book. "Site Reliability Engineering: How Google Runs Production Systems." O'Reilly, 2016.

---

## Synthesis

### 1. Core Knowledge Base

The deep research agent must internalize the following essential knowledge:

**Research methodology fundamentals**:
- The scoping review framework (Arksey & O'Malley) is the most appropriate systematic review methodology for AI agent research tasks, as it handles heterogeneous sources and allows iterative refinement
- Research should follow a structured 6-phase process: Prompt Analysis, Query Generation, Broad Sweep, Deep Dive, Cross-Reference, Synthesis
- The PRISMA flow model (Identification > Screening > Eligibility > Inclusion) maps directly to web search > snippet evaluation > full content assessment > finding extraction
- Research saturation is reached when 3+ independent searches return substantially the same key points

**Search query construction rules**:
- Always use specific technical terminology, version numbers, and year qualifiers
- Construct 2-4 diverse queries per question using different framings
- Use the four bias-mitigation queries for every technology: benefits, drawbacks, comparisons, real-world experience
- Primary sources (official docs, RFCs) take precedence over secondary sources (blogs, tutorials)
- The source quality hierarchy: Official docs > Conference talks > Expert blogs > Tutorials > General blogs > Vendor marketing

**Source evaluation (CRAAP adapted for technical content)**:
- Currency: For technology topics, content older than 2-3 years should be flagged; for rapidly evolving areas, even 12 months may be stale
- Relevance: Content must address the specific question, not just the general topic
- Authority: Named authors with verifiable credentials and production experience are most trustworthy
- Accuracy: Look for specific examples, benchmarks, and trade-off acknowledgment
- Purpose: Distinguish between content that informs (good) and content that sells (suspect)

**Synthesis organization**:
- Every finding must map to at least one of the five synthesis categories
- Use thematic synthesis: extract findings > group by theme > derive analytical insights
- Decision frameworks must include conditions, not just recommendations
- Anti-patterns must include consequences and alternatives
- Tool recommendations must include selection criteria and version information

**Output quality standards**:
- Every finding must have source attribution
- Confidence levels (HIGH/MEDIUM/LOW/GAP) must accompany all claims
- Specificity test: Could a non-expert build an effective agent from this output alone?
- Detail test: Is each finding a 1-3 sentence actionable statement?
- Coverage test: Do all research prompt sub-questions have at least one substantive answer?

### 2. Decision Frameworks

**When to broaden a search** (query returning < 3 relevant results):
1. First try: Use alternative terminology (synonyms, related concepts)
2. Second try: Search adjacent domains that might discuss the same concept
3. Third try: Search for expert names in the field and find their content directly
4. Last resort: Document the gap explicitly with the queries attempted

**When to stop researching a topic**:
- 3+ independent sources confirm the same key findings
- All sub-questions have at least one substantive answer
- New searches return information already captured
- Practical, actionable recommendations can be written for the topic

**When sources conflict**:
- If one source is official documentation and the other is a blog: Prefer official documentation
- If both are practitioner experience: Document both perspectives with their contextual assumptions
- If the conflict is temporal: Prefer the more recent source, but verify the older approach is actually superseded
- If the conflict is genuinely unresolvable: Present both perspectives with clear context framing

**How to allocate research effort across topics**:
- Proportional to the number of sub-questions in each area
- Increase allocation for areas with contradictions or gaps
- Decrease allocation for areas reaching saturation
- No single topic should consume more than 25% of total search effort
- Every topic gets a minimum of 2 searches regardless

**How to adapt research depth by agent archetype**:
- Architect agents: Deep on trade-offs and decision frameworks; moderate on implementation details
- Domain Expert agents: Very deep on specific tools and techniques; limited on adjacent domains
- Enforcer agents: Comprehensive on rules and criteria; shallow on implementation
- Orchestrator agents: Broad across many domains; shallow depth in each
- Reviewer agents: Moderate depth on quality criteria; shallow on implementation

**When to flag a finding as uncertain**:
- HIGH confidence: 3+ independent authoritative sources agree
- MEDIUM confidence: 2 sources agree or one highly authoritative source
- LOW confidence: Single source only, especially if it is a blog or tutorial
- GAP: No findings despite 3+ search attempts with varied queries

### 3. Anti-Patterns Catalog

**1. Hallucination Filling**
- Description: When search results are sparse, the agent generates plausible-sounding "findings" from its training data without source attribution
- Why harmful: Creates fabricated knowledge that the downstream agent will treat as verified truth
- Detection: Any finding without a specific source URL or citation
- Prevention: Strict rule -- no finding without source attribution. Document gaps rather than fill them.

**2. Confirmation Bias in Search**
- Description: Only searching for evidence that supports the expected answer, ignoring contradictory evidence
- Why harmful: Produces one-sided research that misses important trade-offs and limitations
- Detection: All findings for a technology are positive; no limitations or alternatives documented
- Prevention: Mandatory bias-mitigation protocol -- search for benefits, drawbacks, comparisons, and real-world experience for every topic

**3. Vendor Content as Technical Truth**
- Description: Accepting marketing materials from tool vendors as objective technical guidance
- Why harmful: Vendor content systematically overstates benefits and understates limitations
- Detection: Source is a vendor website or vendor-authored blog; content has no trade-offs or limitations
- Prevention: Apply CRAAP Purpose criterion rigorously; always seek independent practitioner validation

**4. Single-Source Dependency**
- Description: Building an entire research area's findings on one source
- Why harmful: If that source is wrong, biased, or outdated, all derived knowledge is compromised
- Detection: A research area has only one cited source
- Prevention: Minimum 3 independent sources per research area; 2 for any individual claim

**5. Recency Worship**
- Description: Recommending the newest tools and approaches while dismissing established, proven alternatives
- Why harmful: New does not mean better; established tools often have better ecosystem support and documentation
- Detection: All recommendations are for tools released in the last 12 months
- Prevention: Include searches for "established best practices" and "time-tested approaches" alongside current trends

**6. Scope Creep in Research**
- Description: Following interesting tangents that expand beyond the research prompt's defined scope
- Why harmful: Wastes context window capacity on irrelevant findings; delays coverage of assigned topics
- Detection: Research output contains sections that don't map to any question in the research prompt
- Prevention: Before adding any finding, verify it answers a specific question from the prompt

**7. Premature Convergence**
- Description: Declaring a topic "researched" after finding initial results that seem comprehensive
- Why harmful: May miss important nuances, contradictions, or emerging practices
- Detection: Some research areas have 10+ findings while others have 1-2
- Prevention: Mandatory coverage check against all sub-questions before concluding any area

**8. Echo Chamber Searching**
- Description: Searching only within familiar sources and domains, missing diverse perspectives
- Why harmful: Produces research that reflects one community's views, not the broader landscape
- Detection: All sources come from the same platform (e.g., all Medium, all Stack Overflow)
- Prevention: Search across multiple platforms: official docs, conference talks, practitioner blogs, academic papers

**9. Ignoring Context in Contradictions**
- Description: When two sources disagree, dismissing one as "wrong" rather than investigating contextual factors
- Why harmful: The "wrong" source may be correct in a different context that the agent's users will encounter
- Detection: Research output never presents alternative viewpoints or conditional recommendations
- Prevention: Always investigate WHY sources disagree before choosing one perspective

**10. Depth Without Breadth**
- Description: Exhaustively researching one area while leaving others barely covered
- Why harmful: The resulting agent will be an expert in one subtopic and dangerously ignorant in others
- Detection: One research area has 20+ findings while another has 2
- Prevention: Time-boxing with hard limits (no area > 25% of effort) and minimum coverage requirements

### 4. Tool & Technology Map

#### Search Phase Tools and Strategies

**Query construction patterns**:
| Pattern | Template | Use Case |
|---------|----------|----------|
| Current practice | `"[technology] best practices [year]"` | Finding consensus approaches |
| Anti-pattern | `"[technology] anti-patterns mistakes avoid"` | Finding what NOT to do |
| Comparison | `"[tool A] vs [tool B] comparison [year]"` | Technology selection |
| Production experience | `"[technology] production experience lessons learned"` | Real-world validation |
| Official docs | `"site:[official-domain] [topic]"` | Primary sources |
| Post-mortems | `"[technology] postmortem incident"` | Failure knowledge |
| Emerging trends | `"[domain] trends emerging [year]"` | Forward-looking research |
| Expert content | `"[expert name] [topic]"` | Following known authorities |

**Authoritative domains for site-specific searching**:
- Cloud: `site:docs.aws.amazon.com`, `site:cloud.google.com/docs`, `site:learn.microsoft.com`
- Standards: `site:rfc-editor.org`, `site:ietf.org`, `site:w3.org`
- Security: `site:owasp.org`, `site:nvd.nist.gov`, `site:cve.mitre.org`
- Research: `site:arxiv.org`, `site:dl.acm.org`, `site:scholar.google.com`
- DevOps: `site:kubernetes.io`, `site:docs.docker.com`, `site:terraform.io`
- Engineering blogs: `site:engineering.fb.com`, `site:netflixtechblog.com`, `site:blog.cloudflare.com`

#### Evaluation Phase Frameworks

**CRAAP scoring rubric** (adapted for automation):
For each source, score 1-5 on each dimension:
- Currency: 5 = published within 6 months; 3 = 1-2 years; 1 = 3+ years
- Relevance: 5 = directly answers the question; 3 = partially relevant; 1 = tangentially related
- Authority: 5 = official docs or recognized expert; 3 = experienced practitioner; 1 = unknown author
- Accuracy: 5 = includes evidence, benchmarks, trade-offs; 3 = reasonable claims without evidence; 1 = vague or unsupported
- Purpose: 5 = educational/informational; 3 = mixed; 1 = primarily promotional

Sources scoring 20+ (out of 25) are high quality. 15-19 are acceptable. Below 15 should be used with caution and corroborated.

#### Synthesis Phase Organization

**Five-category mapping template**:
```
## Core Knowledge Base
- [Definitive statement]: [source] [confidence]

## Decision Frameworks
- When [condition], use [approach] because [reason]: [source] [confidence]
- Alternative: When [different condition], use [different approach] instead

## Anti-Patterns Catalog
- [Pattern name]: [What it looks like] -> [Why it's harmful] -> [What to do instead]: [source]

## Tool & Technology Map
- [Category]: [Tool 1] (open-source, [key feature]), [Tool 2] (commercial, [key feature])
  - Selection criteria: [When to choose each]

## Interaction Scripts
- Trigger: "[Common user request]"
- Response pattern: [What the agent should do/ask/recommend]
```

### 5. Interaction Scripts

#### Script 1: Receiving a Research Prompt

**Trigger**: Agent receives a research prompt file path or content
**Response pattern**:
1. Read and parse the research prompt
2. Extract: Objective, Context, Research Areas (with all sub-questions), Synthesis Requirements, Integration Points
3. Count total sub-questions across all research areas
4. Plan search budget: [total sub-questions] * 2 searches minimum, allocate proportionally
5. Identify any research areas that depend on findings from other areas (sequencing)
6. Begin with Phase 1: Broad Sweep (1-2 searches per area)

#### Script 2: Executing a Search for a Sub-Question

**Trigger**: A specific sub-question needs to be researched
**Response pattern**:
1. Formulate 2-4 search queries using different framings:
   - Direct question form
   - Best practices form
   - Problem/anti-pattern form
   - Comparison/alternatives form
2. Execute searches
3. For each result: evaluate snippet for relevance (screening)
4. For promising results: fetch full content (eligibility)
5. Extract specific findings with source attribution
6. Assess confidence level
7. Map findings to appropriate synthesis categories
8. Check: Has this question been sufficiently answered?

#### Script 3: Handling Insufficient Search Results

**Trigger**: A sub-question has < 3 relevant results after initial searches
**Response pattern**:
1. Log the failed queries for the research output
2. Reformulate using alternative terminology
3. Try adjacent domain searches
4. Try expert-specific searches
5. Try official documentation site-specific searches
6. If still insufficient after 4 attempts: document as a GAP with all queries attempted
7. Never fabricate findings to fill gaps

#### Script 4: Resolving Contradictions

**Trigger**: Two or more sources provide conflicting information
**Response pattern**:
1. Document both claims with their sources
2. Check if the contradiction is contextual (different use cases, scales, industries)
3. Check if the contradiction is temporal (older vs. newer practice)
4. Check relative authority of sources (CRAAP scores)
5. If resolvable: document the resolution and reasoning
6. If not resolvable: present both perspectives with clear context framing
7. Flag the finding as MEDIUM confidence with the contradiction noted

#### Script 5: Producing the Final Synthesis Document

**Trigger**: All research areas have been covered (or time budget exhausted)
**Response pattern**:
1. Review coverage: check every sub-question has at least one finding
2. Identify and fill critical gaps (areas with no findings)
3. Organize findings into the five synthesis categories
4. Write the Core Knowledge Base section: definitive statements with sources
5. Write the Decision Frameworks section: conditional recommendations with reasoning
6. Write the Anti-Patterns Catalog: named patterns with consequences and alternatives
7. Write the Tool & Technology Map: categorized tools with selection criteria
8. Write the Interaction Scripts: common scenarios with response patterns
9. Add metadata: research methodology, confidence levels, identified gaps, date of research
10. Write the output file to the specified path

#### Script 6: Adapting Research to Agent Archetype

**Trigger**: Research prompt indicates a specific agent type (architect, domain expert, enforcer, orchestrator, reviewer)
**Response pattern**:
1. Identify the agent archetype from the prompt's objective and context
2. Adjust research depth:
   - Architect: Prioritize trade-off analysis and decision frameworks
   - Domain Expert: Prioritize tool-specific depth and configuration details
   - Enforcer: Prioritize rule definitions and compliance criteria
   - Orchestrator: Prioritize workflow patterns and delegation logic
   - Reviewer: Prioritize quality criteria and defect patterns
3. Adjust source preferences:
   - Architect: Conference talks, architecture blogs, ADRs from open-source projects
   - Domain Expert: Official documentation, tool-specific deep dives, performance benchmarks
   - Enforcer: Standards documents, regulatory guidance, compliance frameworks
   - Orchestrator: Workflow documentation, integration guides, coordination patterns
   - Reviewer: Quality frameworks, testing best practices, defect taxonomies
4. Adjust synthesis category emphasis:
   - Architect: Decision Frameworks gets the most detail
   - Domain Expert: Core Knowledge Base gets the most detail
   - Enforcer: Anti-Patterns Catalog gets the most detail
   - Orchestrator: Interaction Scripts gets the most detail
   - Reviewer: Anti-Patterns Catalog and Decision Frameworks get the most detail

#### Script 7: Mid-Research Progress Assessment

**Trigger**: Completed the Broad Sweep phase (initial searches for all areas)
**Response pattern**:
1. Count findings per research area
2. Identify areas below minimum threshold (< 2 findings per sub-question)
3. Identify areas with contradictions needing resolution
4. Identify areas approaching saturation (3+ sources confirming same findings)
5. Reallocate remaining search budget:
   - More searches for under-covered areas
   - Contradiction resolution searches for conflicting areas
   - Skip or minimize searches for saturated areas
6. Begin Deep Dive phase with the reallocated budget

#### Script 8: Quality Self-Check Before Writing Output

**Trigger**: All research is complete, about to write the synthesis document
**Response pattern**:
Verify against quality criteria:
- [ ] Every sub-question in the research prompt has at least one finding
- [ ] Every finding has source attribution
- [ ] Every finding has a confidence level
- [ ] No finding is based on a single vendor source without corroboration
- [ ] All five synthesis categories have substantive content
- [ ] Contradictions are documented with resolution or explicit framing
- [ ] Gaps are documented with queries attempted
- [ ] The output passes the "Agent Builder Test" (could a non-expert build an agent from this?)
- [ ] Research areas are proportionally covered (no area > 3x the findings of another)
- [ ] Findings are specific and actionable (not generic platitudes)

If any criterion fails, address the deficiency before writing the output.
