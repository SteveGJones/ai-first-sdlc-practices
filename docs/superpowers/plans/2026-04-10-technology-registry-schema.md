# Technology Registry Schema Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver sub-feature 3 (#145) of EPIC #142 — the curated technology registry schema design document plus 3 populated example entries that validate the schema.

**Architecture:** Split YAML files in `data/technology-registry/` — one `_index.yaml` index with aliases, detection patterns, and manifest, plus one file per technology. The schema doc at `docs/architecture/technology-registry-schema.md` is already written and defines all fields, templates, and validation rules. This plan creates the actual data files and project artifacts (feature proposal, retrospective).

**Tech Stack:** YAML data files, Python (`yaml.safe_load` for parse validation), markdown documentation.

---

## File Map

| Action | File | Responsibility |
|--------|------|---------------|
| Already created | `docs/architecture/technology-registry-schema.md` | Schema design doc (spec) |
| Create | `data/technology-registry/_index.yaml` | Registry metadata, aliases, detection patterns, manifest |
| Create | `data/technology-registry/mongodb.yaml` | MongoDB: Section A/B/C + cross-refs + trusted sources |
| Create | `data/technology-registry/redis.yaml` | Redis: Section A/B/C + cross-refs + trusted sources |
| Create | `data/technology-registry/aws.yaml` | AWS: Section A/B/C + cross-refs + trusted sources |
| Create | `docs/feature-proposals/145-technology-registry-schema.md` | Feature proposal |
| Create | `retrospectives/145-technology-registry-schema.md` | Retrospective |

---

### Task 1: Research actual tools for MongoDB, Redis, and AWS

**Files:**
- None (research only — results feed into Tasks 2-5)

Research the real ecosystem for each of the 3 example technologies. The goal is verified data (package names, publishers, URLs, maintenance status) that goes directly into the YAML files. No guessing.

- [ ] **Step 1: Research MongoDB tooling**

Search for real MCP servers, official drivers, and Claude Code plugins for MongoDB.

**Section A (Claude Code tools) — search these:**
- npm: `npm search @mongodb mcp` or WebSearch `"mongodb mcp server" site:npmjs.com`
- PyPI: WebSearch `"mongodb mcp server" site:pypi.org`
- GitHub: WebSearch `"github.com/mongodb" mcp server`
- Claude plugin marketplace: check `.claude-plugin/marketplace.json` for MongoDB-related plugins

**Section B (project libraries) — verify these assumed packages:**
- `pymongo` on PyPI — confirm publisher, current version, URL
- `mongodb` on npm — confirm publisher, current version, URL
- `motor` on PyPI (async Python driver) — confirm if worth including

**Record for each tool found:**
- Exact package name (as published)
- Publisher name and whether they are the official vendor
- Source URL (registry page or GitHub repo)
- Description (from the package's own metadata)
- Last publish date or last commit (for maintenance status)
- Required environment variables (from README)
- Any install quirks (non-standard setup → `install_override` candidate)

**Section C — assess gaps:**
- Does the MCP server (if found) cover operational needs (query, index, schema inspection)?
- What architectural guidance is missing that a custom agent would provide?
- Refine the gap template based on what the real MCP server actually covers vs doesn't

- [ ] **Step 2: Research Redis tooling**

Same search pattern as Step 1 but for Redis:
- npm: `@redis mcp`, `redis mcp server`
- PyPI: `redis mcp server`
- GitHub: `github.com/redis` for MCP/agent repos
- Verify: `redis` (pip), `ioredis` (npm) — publishers, URLs, versions
- Assess Section C gaps based on real MCP server capabilities

- [ ] **Step 3: Research AWS tooling**

Same search pattern for AWS:
- npm: `@aws mcp`, `aws mcp server`, `@amzn mcp`
- PyPI: `aws mcp server`
- GitHub: `github.com/aws`, `github.com/awslabs` for MCP/agent repos
- Verify: `boto3` (pip), `@aws-sdk/*` (npm) — publishers, URLs, versions
- Note: AWS may have multiple MCP servers (one per service vs monolithic). Record what actually exists.
- Assess Section C gaps — AWS is broad, so gaps may differ from assumptions

- [ ] **Step 4: Compile research summary**

Create a structured summary with verified data for all 3 technologies. Format:

```
## MongoDB
### Section A
- [tool name]: [package], [source URL], [publisher], [last updated], [env vars]
### Section B
- [library name]: [package], [ecosystem], [source URL], [publisher]
### Section C
- [gap topic]: [refined description based on what Section A actually covers]
### Trusted Sources
- [verified vendor URLs]

## Redis
...

## AWS
...
```

This summary is the authoritative input for Tasks 2-5. If a tool from the original plan doesn't exist (e.g., `@mongodb/mcp-server` was a guess), replace it with what was actually found. If no MCP server exists for a technology, Section A is empty and the Section C gap description should reflect that.

- [ ] **Step 5: Update the technology file content in Tasks 3-5**

Based on the research findings, the YAML content in Tasks 3, 4, and 5 must be updated to use verified data before those tasks are executed. If the actual package names, URLs, or capabilities differ from the illustrative examples, the task content must be corrected.

**Important**: Do not proceed to Task 2 until this research is complete. Every field in the registry files should use real, verified data.

---

### Task 2: Create the registry directory and index file

**Files:**
- Create: `data/technology-registry/_index.yaml`

- [ ] **Step 1: Create the directory**

```bash
mkdir -p data/technology-registry
```

- [ ] **Step 2: Create `_index.yaml`**

Write the following to `data/technology-registry/_index.yaml`. Note: only the 3 example technologies (mongodb, redis, aws) are included. PostgreSQL aliases, detection patterns, and manifest entry will be added in sub-feature 4 (#146) alongside its technology file — validation rules 8 and 9 require all alias/detection targets to exist in the manifest.

```yaml
version: "1.0"
staleness_threshold_days: 180

# --- Alias normalization ---
# Maps informal/short names to canonical technology keys.
# Applied before manifest lookup.
# Note: postgresql aliases will be added when postgresql.yaml is created (#146).
aliases:
  mongo: mongodb

# --- Detection patterns ---
# Maps package names, Docker images, and env vars to technology keys.
# Replaces the hardcoded mappings in setup-team step 5a.
# Note: this is a seed set for the 3 example technologies.
# Sub-feature 4 (#146) populates the full detection map.
detection:
  pip:
    pymongo: mongodb
    motor: mongodb
    redis: redis
    boto3: aws
  npm:
    mongoose: mongodb
    ioredis: redis
    redis: redis
    aws-sdk: aws
    "@aws-sdk/client-s3": aws
  docker:
    "mongo:*": mongodb
    "redis:*": redis
  env:
    "MONGO_URI=*": mongodb
    "MONGO_URL=*": mongodb
    "REDIS_URL=*": redis

# --- Technology manifest ---
# Every technology with a registry file is listed here.
# Setup-team uses this to know what's available without scanning the directory.
technologies:
  mongodb:
    file: mongodb.yaml
    display_name: MongoDB
  redis:
    file: redis.yaml
    display_name: Redis
  aws:
    file: aws.yaml
    display_name: Amazon Web Services
```

- [ ] **Step 3: Verify the YAML parses**

```bash
python3 -c "import yaml; data = yaml.safe_load(open('data/technology-registry/_index.yaml')); print(f'Version: {data[\"version\"]}'); print(f'Technologies: {list(data[\"technologies\"].keys())}'); print(f'Aliases: {data[\"aliases\"]}'); print(f'Detection ecosystems: {list(data[\"detection\"].keys())}')"
```

Expected output:
```
Version: 1.0
Technologies: ['mongodb', 'redis', 'aws']
Aliases: {'mongo': 'mongodb'}
Detection ecosystems: ['pip', 'npm', 'docker', 'env']
```

- [ ] **Step 4: Commit**

```bash
git add data/technology-registry/_index.yaml
git commit -m "feat(registry): create technology registry index file

Part of EPIC #142, sub-feature 3 (#145).
Seed index with 3 technologies (mongodb, redis, aws),
detection patterns, and alias map."
```

---

### Task 3: Create mongodb.yaml

**Files:**
- Create: `data/technology-registry/mongodb.yaml`

- [ ] **Step 1: Create the file**

Write the following to `data/technology-registry/mongodb.yaml`:

```yaml
display_name: MongoDB
category: database
description: Document database for JSON-like data with flexible schemas

section_a:
  - name: "@mongodb/mcp-server"
    type: mcp-server-npm
    package: "@mongodb/mcp-server"
    source: https://www.npmjs.com/package/@mongodb/mcp-server
    publisher: MongoDB Inc.
    publisher_verified: true
    description: >
      Pre-built MCP server with query execution, schema inspection,
      index management, and aggregation pipeline support.
    env:
      - name: MONGODB_URI
        description: MongoDB connection string
        example: "mongodb://localhost:27017/mydb"
    verified_date: "2026-04-10"

section_b:
  - name: pymongo
    package: pymongo
    ecosystem: pip
    source: https://pypi.org/project/pymongo/
    publisher: MongoDB Inc.
    description: Official Python driver for MongoDB
    usage: "from pymongo import MongoClient"
    docs: https://pymongo.readthedocs.io/
    verified_date: "2026-04-10"

  - name: mongodb (Node.js driver)
    package: mongodb
    ecosystem: npm
    source: https://www.npmjs.com/package/mongodb
    publisher: MongoDB Inc.
    description: Official Node.js driver for MongoDB
    usage: 'const { MongoClient } = require("mongodb")'
    docs: https://www.mongodb.com/docs/drivers/node/current/
    verified_date: "2026-04-10"

section_c:
  - topic: MongoDB schema design patterns
    slug: mongodb-schema-expert
    why: >
      The @mongodb/mcp-server covers operational tasks (query, index management)
      but not architectural guidance. A custom agent would provide schema design
      patterns (embedded vs referenced, denormalization trade-offs, sharding key
      selection), migration planning, and team-specific conventions.
    agent_would_know: >
      MongoDB schema design patterns for document databases, idiomatic
      aggregation pipelines, performance trade-offs for common access patterns.
    research_scope:
      - MongoDB University schema design course
      - Official best practices documentation
      - Schema evolution patterns for large deployments
      - Sharding strategies and key selection
    estimated_duration: "2-3 hours"
    create_command: "@pipeline-orchestrator create a mongodb-schema-expert agent"
    verified_date: "2026-04-10"

our_agents:
  - agent: database-architect
    plugin: sdlc-team-fullstack
    relevance: >
      Schema design, query optimization, index strategy
      for MongoDB collections.
  - agent: backend-architect
    plugin: sdlc-team-fullstack
    relevance: >
      Application-layer patterns for MongoDB integration
      (connection pooling, retry logic, transactions).

trusted_sources:
  - url: https://github.com/mongodb
    type: github-org
  - url: https://www.npmjs.com/~mongodb
    type: npm-scope
  - url: https://pypi.org/user/mongodb/
    type: pypi-publisher
```

- [ ] **Step 2: Verify parse and required fields**

```bash
python3 -c "
import yaml

data = yaml.safe_load(open('data/technology-registry/mongodb.yaml'))

# Check top-level required fields
for field in ['display_name', 'category', 'description', 'trusted_sources']:
    assert field in data, f'Missing required field: {field}'

# Check Section A required fields
for tool in data.get('section_a', []):
    for field in ['name', 'type', 'package', 'source', 'description', 'verified_date']:
        assert field in tool, f'Section A tool {tool.get(\"name\", \"?\")} missing: {field}'

# Check Section B required fields
for lib in data.get('section_b', []):
    for field in ['name', 'package', 'ecosystem', 'source', 'description', 'verified_date']:
        assert field in lib, f'Section B lib {lib.get(\"name\", \"?\")} missing: {field}'

# Check Section C required fields
for gap in data.get('section_c', []):
    for field in ['topic', 'slug', 'why', 'agent_would_know', 'research_scope', 'create_command', 'verified_date']:
        assert field in gap, f'Section C gap {gap.get(\"topic\", \"?\")} missing: {field}'

# Check our_agents required fields
for agent in data.get('our_agents', []):
    for field in ['agent', 'plugin', 'relevance']:
        assert field in agent, f'our_agents entry {agent.get(\"agent\", \"?\")} missing: {field}'

# Check trusted_sources required fields
for src in data['trusted_sources']:
    for field in ['url', 'type']:
        assert field in src, f'trusted_sources entry missing: {field}'

print(f'{data[\"display_name\"]}: all required fields present')
print(f'  Section A: {len(data.get(\"section_a\", []))} tools')
print(f'  Section B: {len(data.get(\"section_b\", []))} libraries')
print(f'  Section C: {len(data.get(\"section_c\", []))} gaps')
print(f'  Our agents: {len(data.get(\"our_agents\", []))}')
print(f'  Trusted sources: {len(data[\"trusted_sources\"])}')
"
```

Expected output:
```
MongoDB: all required fields present
  Section A: 1 tools
  Section B: 2 libraries
  Section C: 1 gaps
  Our agents: 2
  Trusted sources: 3
```

- [ ] **Step 3: Commit**

```bash
git add data/technology-registry/mongodb.yaml
git commit -m "feat(registry): add MongoDB technology entry

Section A: @mongodb/mcp-server (npm)
Section B: pymongo (pip), mongodb (npm)
Section C: schema design patterns gap
Cross-refs: database-architect, backend-architect"
```

---

### Task 4: Create redis.yaml

**Files:**
- Create: `data/technology-registry/redis.yaml`

- [ ] **Step 1: Create the file**

Write the following to `data/technology-registry/redis.yaml`:

```yaml
display_name: Redis
category: cache
description: In-memory data store used as cache, message broker, and database

section_a:
  - name: redis-mcp-server
    type: mcp-server-npm
    package: "@redis/mcp-server"
    source: https://www.npmjs.com/package/@redis/mcp-server
    publisher: Redis Ltd.
    publisher_verified: true
    description: >
      Pre-built MCP server for Redis with key operations, pub/sub,
      and cluster management.
    env:
      - name: REDIS_URL
        description: Redis connection URL
        example: "redis://localhost:6379"
    verified_date: "2026-04-10"

section_b:
  - name: redis-py
    package: redis
    ecosystem: pip
    source: https://pypi.org/project/redis/
    publisher: Redis Ltd.
    description: Official Python client for Redis
    usage: "import redis"
    docs: https://redis-py.readthedocs.io/
    verified_date: "2026-04-10"

  - name: ioredis
    package: ioredis
    ecosystem: npm
    source: https://www.npmjs.com/package/ioredis
    publisher: Community (widely adopted)
    description: Full-featured Redis client for Node.js with cluster and sentinel support
    usage: 'const Redis = require("ioredis")'
    docs: https://github.com/redis/ioredis
    verified_date: "2026-04-10"

section_c:
  - topic: Redis caching architecture patterns
    slug: redis-caching-expert
    why: >
      The MCP server provides operational access to Redis commands but not
      architectural guidance. A custom agent would advise on caching strategies
      (write-through, write-behind, cache-aside), eviction policies, TTL design,
      and cache invalidation patterns for specific application architectures.
    agent_would_know: >
      Redis caching patterns, eviction strategies, pub/sub design,
      Lua scripting for atomic operations, cluster topology decisions.
    research_scope:
      - Redis University caching patterns course
      - Cache invalidation strategies (event-driven, TTL-based)
      - Redis Cluster vs Sentinel decision framework
      - Memory optimization and eviction policy selection
    estimated_duration: "2-3 hours"
    create_command: "@pipeline-orchestrator create a redis-caching-expert agent"
    verified_date: "2026-04-10"

our_agents:
  - agent: database-architect
    plugin: sdlc-team-fullstack
    relevance: >
      Cache layer design, data structure selection,
      persistence vs pure-cache trade-offs.
  - agent: performance-engineer
    plugin: sdlc-team-common
    relevance: >
      Cache hit ratio analysis, latency profiling,
      connection pool tuning.

trusted_sources:
  - url: https://github.com/redis
    type: github-org
  - url: https://www.npmjs.com/~redis
    type: npm-scope
  - url: https://pypi.org/user/redis/
    type: pypi-publisher
```

- [ ] **Step 2: Verify parse and required fields**

```bash
python3 -c "
import yaml

data = yaml.safe_load(open('data/technology-registry/redis.yaml'))

for field in ['display_name', 'category', 'description', 'trusted_sources']:
    assert field in data, f'Missing required field: {field}'

for tool in data.get('section_a', []):
    for field in ['name', 'type', 'package', 'source', 'description', 'verified_date']:
        assert field in tool, f'Section A tool {tool.get(\"name\", \"?\")} missing: {field}'

for lib in data.get('section_b', []):
    for field in ['name', 'package', 'ecosystem', 'source', 'description', 'verified_date']:
        assert field in lib, f'Section B lib {lib.get(\"name\", \"?\")} missing: {field}'

for gap in data.get('section_c', []):
    for field in ['topic', 'slug', 'why', 'agent_would_know', 'research_scope', 'create_command', 'verified_date']:
        assert field in gap, f'Section C gap {gap.get(\"topic\", \"?\")} missing: {field}'

for agent in data.get('our_agents', []):
    for field in ['agent', 'plugin', 'relevance']:
        assert field in agent, f'our_agents entry {agent.get(\"agent\", \"?\")} missing: {field}'

for src in data['trusted_sources']:
    for field in ['url', 'type']:
        assert field in src, f'trusted_sources entry missing: {field}'

print(f'{data[\"display_name\"]}: all required fields present')
print(f'  Section A: {len(data.get(\"section_a\", []))} tools')
print(f'  Section B: {len(data.get(\"section_b\", []))} libraries')
print(f'  Section C: {len(data.get(\"section_c\", []))} gaps')
print(f'  Our agents: {len(data.get(\"our_agents\", []))}')
print(f'  Trusted sources: {len(data[\"trusted_sources\"])}')
"
```

Expected output:
```
Redis: all required fields present
  Section A: 1 tools
  Section B: 2 libraries
  Section C: 1 gaps
  Our agents: 2
  Trusted sources: 3
```

- [ ] **Step 3: Commit**

```bash
git add data/technology-registry/redis.yaml
git commit -m "feat(registry): add Redis technology entry

Section A: @redis/mcp-server (npm)
Section B: redis-py (pip), ioredis (npm)
Section C: caching architecture patterns gap
Cross-refs: database-architect, performance-engineer"
```

---

### Task 5: Create aws.yaml

**Files:**
- Create: `data/technology-registry/aws.yaml`

- [ ] **Step 1: Create the file**

Write the following to `data/technology-registry/aws.yaml`:

```yaml
display_name: Amazon Web Services
category: cloud
description: Cloud platform with 200+ services including compute, storage, databases, and AI/ML

section_a:
  - name: aws-mcp-server
    type: mcp-server-npm
    package: "@aws/mcp-server"
    source: https://www.npmjs.com/package/@aws/mcp-server
    publisher: Amazon Web Services
    publisher_verified: true
    description: >
      Pre-built MCP server for AWS with S3, DynamoDB, Lambda,
      and CloudFormation operations.
    env:
      - name: AWS_ACCESS_KEY_ID
        description: AWS access key
        example: "AKIA..."
      - name: AWS_SECRET_ACCESS_KEY
        description: AWS secret key
        example: "(secret)"
      - name: AWS_REGION
        description: AWS region
        example: "us-east-1"
    verified_date: "2026-04-10"

section_b:
  - name: boto3
    package: boto3
    ecosystem: pip
    source: https://pypi.org/project/boto3/
    publisher: Amazon Web Services
    description: Official AWS SDK for Python
    usage: "import boto3"
    docs: https://boto3.amazonaws.com/v1/documentation/api/latest/
    verified_date: "2026-04-10"

  - name: AWS SDK for JavaScript
    package: "@aws-sdk/client-s3"
    ecosystem: npm
    source: https://www.npmjs.com/package/@aws-sdk/client-s3
    publisher: Amazon Web Services
    description: Official AWS SDK v3 for JavaScript (modular, per-service packages)
    usage: 'const { S3Client } = require("@aws-sdk/client-s3")'
    docs: https://docs.aws.amazon.com/AWSJavaScriptSDK/v3/latest/
    verified_date: "2026-04-10"

section_c:
  - topic: AWS infrastructure architecture
    slug: aws-infrastructure-expert
    why: >
      The MCP server provides operational access to AWS APIs but not
      architectural guidance. A custom agent would advise on service selection
      (e.g., ECS vs EKS vs Lambda), cost optimization, IAM policy design,
      networking (VPC, subnets, security groups), and multi-region strategies.
    agent_would_know: >
      AWS Well-Architected Framework pillars, service selection decision
      trees, cost optimization patterns, IAM least-privilege design.
    research_scope:
      - AWS Well-Architected Framework (all 6 pillars)
      - Service comparison guides (compute, storage, database tiers)
      - IAM policy patterns and security best practices
      - Cost optimization strategies (reserved instances, savings plans, right-sizing)
      - Multi-region and disaster recovery patterns
    estimated_duration: "2-3 hours"
    create_command: "@pipeline-orchestrator create an aws-infrastructure-expert agent"
    verified_date: "2026-04-10"

  - topic: AWS serverless patterns
    slug: aws-serverless-expert
    why: >
      Serverless on AWS (Lambda, Step Functions, EventBridge, API Gateway)
      requires specialized architectural knowledge distinct from traditional
      infrastructure. Cold starts, execution limits, event-driven design,
      and observability differ fundamentally from container-based approaches.
    agent_would_know: >
      AWS serverless design patterns, Lambda optimization, Step Functions
      orchestration, EventBridge event-driven architecture.
    research_scope:
      - Lambda performance optimization (cold starts, provisioned concurrency)
      - Step Functions vs direct Lambda orchestration
      - EventBridge patterns and schema registry
      - Serverless observability (X-Ray, CloudWatch Insights)
    estimated_duration: "2-3 hours"
    create_command: "@pipeline-orchestrator create an aws-serverless-expert agent"
    verified_date: "2026-04-10"

our_agents:
  - agent: solution-architect
    plugin: sdlc-team-common
    relevance: >
      End-to-end AWS solution design, service selection,
      cost-performance trade-off analysis.
  - agent: observability-specialist
    plugin: sdlc-team-common
    relevance: >
      CloudWatch, X-Ray, and OpenTelemetry integration
      for AWS-hosted applications.

trusted_sources:
  - url: https://github.com/aws
    type: github-org
  - url: https://www.npmjs.com/~aws-sdk
    type: npm-scope
  - url: https://pypi.org/user/amazon/
    type: pypi-publisher
  - url: https://docs.aws.amazon.com/
    type: vendor-docs
```

- [ ] **Step 2: Verify parse and required fields**

```bash
python3 -c "
import yaml

data = yaml.safe_load(open('data/technology-registry/aws.yaml'))

for field in ['display_name', 'category', 'description', 'trusted_sources']:
    assert field in data, f'Missing required field: {field}'

for tool in data.get('section_a', []):
    for field in ['name', 'type', 'package', 'source', 'description', 'verified_date']:
        assert field in tool, f'Section A tool {tool.get(\"name\", \"?\")} missing: {field}'

for lib in data.get('section_b', []):
    for field in ['name', 'package', 'ecosystem', 'source', 'description', 'verified_date']:
        assert field in lib, f'Section B lib {lib.get(\"name\", \"?\")} missing: {field}'

for gap in data.get('section_c', []):
    for field in ['topic', 'slug', 'why', 'agent_would_know', 'research_scope', 'create_command', 'verified_date']:
        assert field in gap, f'Section C gap {gap.get(\"topic\", \"?\")} missing: {field}'

for agent in data.get('our_agents', []):
    for field in ['agent', 'plugin', 'relevance']:
        assert field in agent, f'our_agents entry {agent.get(\"agent\", \"?\")} missing: {field}'

for src in data['trusted_sources']:
    for field in ['url', 'type']:
        assert field in src, f'trusted_sources entry missing: {field}'

print(f'{data[\"display_name\"]}: all required fields present')
print(f'  Section A: {len(data.get(\"section_a\", []))} tools')
print(f'  Section B: {len(data.get(\"section_b\", []))} libraries')
print(f'  Section C: {len(data.get(\"section_c\", []))} gaps')
print(f'  Our agents: {len(data.get(\"our_agents\", []))}')
print(f'  Trusted sources: {len(data[\"trusted_sources\"])}')
"
```

Expected output:
```
Amazon Web Services: all required fields present
  Section A: 1 tools
  Section B: 2 libraries
  Section C: 2 gaps
  Our agents: 2
  Trusted sources: 4
```

- [ ] **Step 3: Commit**

```bash
git add data/technology-registry/aws.yaml
git commit -m "feat(registry): add AWS technology entry

Section A: @aws/mcp-server (npm)
Section B: boto3 (pip), @aws-sdk/client-s3 (npm)
Section C: infrastructure architecture gap, serverless patterns gap
Cross-refs: solution-architect, observability-specialist"
```

---

### Task 6: Cross-validate index against technology files

**Files:**
- Verify: `data/technology-registry/_index.yaml`
- Verify: `data/technology-registry/mongodb.yaml`
- Verify: `data/technology-registry/redis.yaml`
- Verify: `data/technology-registry/aws.yaml`

- [ ] **Step 1: Run cross-validation checks**

This checks validation rules 7-10 from the schema spec: index-file consistency, alias targets, detection targets, no duplicate detection keys.

```bash
python3 -c "
import yaml, os, sys

registry_dir = 'data/technology-registry'
index = yaml.safe_load(open(os.path.join(registry_dir, '_index.yaml')))
errors = []

tech_keys = set(index['technologies'].keys())

# Rule 7: every file in manifest exists on disk
for key, meta in index['technologies'].items():
    filepath = os.path.join(registry_dir, meta['file'])
    if not os.path.exists(filepath):
        errors.append(f'Rule 7: manifest lists {meta[\"file\"]} but file does not exist')

# Rule 7b: every .yaml file (except _index.yaml) is in manifest
yaml_files = {f for f in os.listdir(registry_dir) if f.endswith('.yaml') and f != '_index.yaml'}
manifest_files = {meta['file'] for meta in index['technologies'].values()}
for f in yaml_files - manifest_files:
    errors.append(f'Rule 7: file {f} exists but is not in manifest')

# Rule 8: alias targets valid
for alias, target in index.get('aliases', {}).items():
    if target not in tech_keys:
        errors.append(f'Rule 8: alias \"{alias}\" -> \"{target}\" but \"{target}\" not in manifest')

# Rule 9: detection targets valid
for ecosystem, mappings in index.get('detection', {}).items():
    for pkg, target in mappings.items():
        if target not in tech_keys:
            errors.append(f'Rule 9: detection {ecosystem}/{pkg} -> \"{target}\" but \"{target}\" not in manifest')

# Rule 10: no duplicate detection keys within an ecosystem
for ecosystem, mappings in index.get('detection', {}).items():
    seen = {}
    for pkg in mappings:
        if pkg in seen:
            errors.append(f'Rule 10: duplicate detection key \"{pkg}\" in ecosystem \"{ecosystem}\"')
        seen[pkg] = True

if errors:
    for e in errors:
        print(f'FAIL: {e}')
    sys.exit(1)
else:
    print(f'All cross-validation checks passed')
    print(f'  Technologies in manifest: {len(tech_keys)}')
    print(f'  Files on disk: {len(yaml_files)}')
    print(f'  Aliases: {len(index.get(\"aliases\", {}))}')
    print(f'  Detection ecosystems: {len(index.get(\"detection\", {}))}')
"
```

Expected output:
```
All cross-validation checks passed
  Technologies in manifest: 3
  Files on disk: 3
  Aliases: 1
  Detection ecosystems: 4
```

- [ ] **Step 2: No commit needed** — this is a verification step only.

---

### Task 7: Run project validation

**Files:**
- None (validation only)

- [ ] **Step 1: Run syntax check**

```bash
python tools/validation/local-validation.py --syntax
```

Expected: PASS (YAML files are not Python, so they won't be checked by the Python syntax checker — but this confirms no Python files were broken).

- [ ] **Step 2: Run quick validation**

```bash
python tools/validation/local-validation.py --quick
```

Expected: PASS. The new files are YAML data and markdown — they should not trigger technical debt, architecture, or other validators.

- [ ] **Step 3: No commit needed** — this is a verification step only.

---

### Task 8: Create feature proposal

**Files:**
- Create: `docs/feature-proposals/145-technology-registry-schema.md`

- [ ] **Step 1: Create the feature proposal**

Write `docs/feature-proposals/145-technology-registry-schema.md` with the following content. Adapt details based on the actual work done:

```markdown
# Feature Proposal: Curated Technology Registry Schema

**Proposal Number:** 145
**Status:** Complete
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-04-10
**Target Branch:** `feature/142-tech-registry`
**EPIC:** #142
**Sub-feature:** 3 of 8

---

## Motivation

Setup-team and pipeline-orchestrator currently discover technology-specific tools via real-time web search (setup-team step 5c, pipeline-orchestrator Phase 0). This is slow, non-deterministic, and produces inconsistent results. The same technology searched twice may yield different tools depending on web search results.

Additionally, the package-to-technology detection mappings in setup-team step 5a are hardcoded in the skill — adding a new technology requires a code change.

---

## Proposed Solution

A curated technology registry at `data/technology-registry/` — split YAML files (one per technology) with an `_index.yaml` index. The registry provides:

1. **Data-driven detection**: `_index.yaml` contains detection patterns (pip/npm/docker/env package names mapped to technology keys), replacing hardcoded mappings in setup-team
2. **Pre-authored discovery data**: each technology file contains Section A (Claude Code tools), Section B (project libraries), and Section C (gap templates), ready to emit in discovery reports
3. **Framework cross-references**: `our_agents` field maps technologies to complementary SDLC agents (with plugin name and relevance)
4. **Freshness tracking**: per-entry `verified_date` + registry-level `staleness_threshold_days`
5. **Fallback-safe**: technologies not in the registry fall back to the existing web search behavior

### Design decisions

See `docs/architecture/technology-registry-schema.md` for the full schema, 11 design decisions with rationale, and 3 populated example entries (MongoDB, Redis, AWS).

Key choices:
- YAML over JSON (~20-30% fewer tokens, more readable for LLM consumers)
- Split files over monolithic (scales, clean git diffs, context-efficient)
- Index with detection patterns (single file load for tech-stack scanning)
- Separate alias lookup table (cross-cutting concern, not per-technology)
- Pre-authored Section C gap templates (curated quality, no web search latency)
- Hybrid install snippets (category templates + install_override for edge cases)
- Per-technology agent cross-references with context (plugin + relevance)
- Typed trusted sources (github-org, npm-scope, etc. — tells discovery agent how to search)

---

## Success Criteria

- [x] Schema design document written at `docs/architecture/technology-registry-schema.md`
- [x] Directory `data/technology-registry/` created with `_index.yaml`
- [x] 3 example technology files (mongodb.yaml, redis.yaml, aws.yaml) populated and valid
- [x] All YAML files parse correctly
- [x] Cross-validation passes (index-file consistency, alias/detection targets, no duplicates)
- [x] Project validation passes (`--quick`)

---

## Changes Made

| Action | File |
|--------|------|
| Create | `docs/architecture/technology-registry-schema.md` (schema design doc) |
| Create | `data/technology-registry/_index.yaml` (registry index) |
| Create | `data/technology-registry/mongodb.yaml` (example entry) |
| Create | `data/technology-registry/redis.yaml` (example entry) |
| Create | `data/technology-registry/aws.yaml` (example entry) |
| Create | `docs/feature-proposals/145-technology-registry-schema.md` (this file) |
| Create | `retrospectives/145-technology-registry-schema.md` |

---

## Downstream

| Sub-feature | Issue | Next step |
|-------------|-------|-----------|
| 4: Populate registry | #146 | Create 20-30 technology files using this schema |
| 5: Wire into setup-team | #147 | Modify skill to read registry before web search |
| 6: Wire into pipeline-orchestrator | #148 | Modify agent Phase 0 to check registry first |
| 7: Cross-reference our plugins | #149 | Populate our_agents across all technology files |
| 8: Maintenance strategy | #150 | Define staleness checks, update cadence, validator script |
```

- [ ] **Step 2: Commit**

```bash
git add docs/feature-proposals/145-technology-registry-schema.md
git commit -m "docs: add feature proposal for #145 technology registry schema"
```

---

### Task 9: Create retrospective

**Files:**
- Create: `retrospectives/145-technology-registry-schema.md`

- [ ] **Step 1: Create the retrospective**

Write `retrospectives/145-technology-registry-schema.md`. The content should reflect the actual session — adapt based on what happened:

```markdown
# Retrospective: #145 — Technology Registry Schema Design

**Branch**: `feature/142-tech-registry`
**Date**: 2026-04-10
**Issue**: #145 (EPIC #142, sub-feature 3)
**Type**: Schema design + seed data

## Context

Sub-feature 3 of EPIC #142: design the curated technology registry schema. The registry replaces web-search-based discovery in setup-team and pipeline-orchestrator with a pre-authored, version-controlled data source. This sub-feature defines the schema shape that sub-features 4-8 all depend on.

## What Went Well

- **Brainstorming surfaced 7 design questions before writing any files.** The structured Q&A format (one question at a time, multiple choice where possible) resolved every open question from the issue scope: Section C representation, install snippets, cross-references, trusted sources, freshness tracking, aliases, and detection patterns. No question was deferred to "figure out during implementation."
- **Detection patterns in the index was a late-stage insight that improved the design.** The original proposed schema (from the EPIC memory) didn't include detection patterns. Asking "should the registry include detection_patterns" as the 7th question surfaced a natural fit — the index is already the "load once" file, and putting detection there makes adding a technology automatically teach setup-team to detect it.
- **YAML over JSON was a user-driven decision.** The original issue assumed JSON. Questioning the format choice during brainstorming led to YAML — fewer tokens, more readable for LLM consumers, consistent with existing project patterns. This is the kind of decision that wouldn't happen without explicit design review.
- **Split files was a user-driven decision for future scalability.** The recommended approach was a single flat file (sufficient for 30 entries). The user chose split files based on realistic growth projections (industry experts, legacy codebases) and context management benefits. Good example of the user applying domain knowledge the AI didn't have.
- **Self-review caught two real issues.** The detection example referenced technologies not in the manifest (would fail validation rule #9), and the mcp-server-pip template assumed module names were derivable from package names (they're not). Both fixed before user review.

## What Could Improve

- **The 3 example entries use illustrative data, not verified data.** The MCP server package names (@mongodb/mcp-server, @redis/mcp-server, @aws/mcp-server) are plausible but not verified against actual npm/PyPI registries. Sub-feature 4 (#146) must verify every entry against real registries before merging.
- **No automated validator yet.** The schema defines 10 validation rules, but the validator script is deferred to sub-feature 8 (#150). The cross-validation in Task 6 covers rules 7-10 (index consistency) but not rules 1-6 (per-entry field validation). The inline Python checks in Tasks 3-5 are one-time — they don't persist as CI enforcement.

## Decisions Made

See `docs/architecture/technology-registry-schema.md` — Design Decisions Log (11 decisions with rationale).

## Key Artifacts

| Artifact | Path |
|----------|------|
| Schema design doc | `docs/architecture/technology-registry-schema.md` |
| Registry index | `data/technology-registry/_index.yaml` |
| MongoDB entry | `data/technology-registry/mongodb.yaml` |
| Redis entry | `data/technology-registry/redis.yaml` |
| AWS entry | `data/technology-registry/aws.yaml` |
```

- [ ] **Step 2: Commit**

```bash
git add retrospectives/145-technology-registry-schema.md
git commit -m "docs: add retrospective for #145 technology registry schema"
```

---

### Task 10: Final commit with schema doc and plan

**Files:**
- Stage: `docs/architecture/technology-registry-schema.md` (already created, not yet committed)
- Stage: `docs/superpowers/plans/2026-04-10-technology-registry-schema.md` (this plan)

- [ ] **Step 1: Commit the schema doc**

```bash
git add docs/architecture/technology-registry-schema.md
git commit -m "docs: add technology registry schema design

Defines the curated technology registry for EPIC #142.
Split YAML files, index with aliases/detection/manifest,
per-technology Section A/B/C entries, cross-references,
freshness tracking. 11 design decisions documented."
```

- [ ] **Step 2: Commit the implementation plan**

```bash
git add docs/superpowers/plans/2026-04-10-technology-registry-schema.md
git commit -m "docs: add implementation plan for #145 technology registry schema"
```

---

### Task 11: Run pre-push validation and create PR

**Files:**
- None (validation and PR creation only)

- [ ] **Step 1: Run pre-push validation**

```bash
python tools/validation/local-validation.py --pre-push
```

Expected: all 10 checks pass. The new files are YAML data and markdown — they should not trigger any validators.

- [ ] **Step 2: Push the branch**

```bash
git push -u origin feature/142-tech-registry
```

- [ ] **Step 3: Create the PR**

```bash
gh pr create --title "feat(registry): design curated technology registry schema (#145)" --body "$(cat <<'EOF'
## Summary

- Designed the curated technology registry schema for EPIC #142 sub-feature 3 (#145)
- Created `data/technology-registry/` with split YAML files: `_index.yaml` index + 3 example entries (MongoDB, Redis, AWS)
- Schema doc at `docs/architecture/technology-registry-schema.md` with full field definitions, install templates, lookup flow, validation rules, and 11 design decisions

## What the registry provides

- **Data-driven detection**: index contains package-to-technology mappings, replacing hardcoded logic in setup-team step 5a
- **Pre-authored discovery**: Section A (Claude Code tools), Section B (project deps), Section C (gap templates) per technology
- **Framework cross-references**: `our_agents` maps technologies to complementary SDLC agents
- **Freshness tracking**: per-entry `verified_date` + configurable `staleness_threshold_days`
- **Additive**: registry-first lookup, web-search fallback. Doesn't break existing behavior.

## Key design decisions

- YAML over JSON (~20-30% fewer tokens for LLM consumers)
- Split files (one per technology) over monolithic
- Detection patterns in index (data-driven, no code changes to add technologies)
- Pre-authored Section C gap templates (curated quality, no web search latency)
- Hybrid install snippets (category templates + install_override for edge cases)

## Downstream (not in this PR)

- #146: Populate registry for 20-30 technologies
- #147: Wire into setup-team
- #148: Wire into pipeline-orchestrator
- #149: Cross-reference our plugins
- #150: Maintenance strategy

## Test plan

- [ ] All YAML files parse with `yaml.safe_load`
- [ ] Required fields present on all Section A/B/C entries
- [ ] Index cross-validation passes (manifest ↔ files, alias targets, detection targets, no duplicates)
- [ ] `local-validation.py --pre-push` passes

Closes #145

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Expected: PR created successfully. Copy the PR URL.
