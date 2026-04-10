# Technology Registry Schema

**Sub-feature**: #145 (EPIC #142)
**Status**: Design
**Date**: 2026-04-10

## Overview

The curated technology registry provides a fast, deterministic lookup for technology-specific tooling recommendations. It replaces the web-search-based discovery in setup-team (step 5c) and pipeline-orchestrator (Phase 0) with a pre-authored, version-controlled data source — falling back to web search only for technologies not in the registry.

### Goals

1. Eliminate web-search latency for the top 20-30 technologies
2. Provide curated, high-quality Section A/B/C entries with verified install instructions
3. Make technology detection data-driven (no hardcoded package-to-technology mappings)
4. Cross-reference third-party tools with the framework's own plugins and agents
5. Support freshness tracking and schema validation for ongoing maintenance

### Non-goals

- Runtime auto-discovery of new technologies (that remains the web-search fallback)
- Replacing the pipeline-orchestrator's full research pipeline (Section C gaps still route there)
- Hosting the registry as a service (it ships as files in the framework repo)

## Directory Structure

```
data/technology-registry/
  _index.yaml              # Registry metadata, aliases, detection, manifest
  mongodb.yaml             # One file per technology
  redis.yaml
  aws.yaml
  postgresql.yaml
  ...
```

**Why split files**: Git diffs are clean (updating MongoDB doesn't touch Redis), context-efficient for LLM consumers (load only the technologies you need), and scales beyond 30 entries without a monolithic file.

**Why YAML**: The primary consumers are LLMs (setup-team skill, pipeline-orchestrator agent). YAML is ~20-30% fewer tokens than equivalent JSON, more readable for both humans and LLMs, and already used elsewhere in this project (`release-mapping.yaml`, `agent-compositions.yaml`). Python validation scripts can parse it with `yaml.safe_load`.

## Index File: `_index.yaml`

The index is the single file loaded at the start of every discovery session. It provides alias normalization, detection pattern matching, and a manifest of available technology files.

```yaml
version: "1.0"
staleness_threshold_days: 180

# --- Alias normalization ---
# Maps informal/short names to canonical technology keys.
# Applied before manifest lookup.
aliases:
  # Databases
  mongo: mongodb
  pg: postgresql
  postgres: postgresql
  psql: postgresql
  mysql2: mysql
  es: elasticsearch
  elastic: elasticsearch
  opensearch: elasticsearch
  sqlite3: sqlite
  # Cloud
  amazon: aws
  dynamodb: aws
  s3: aws
  lambda: aws
  gcloud: gcp
  "google cloud": gcp
  firebase: gcp
  # Messaging
  confluent: kafka
  amqp: rabbitmq
  "apache flink": flink
  # ... plus framework, DevOps, and service aliases (46 total)

# --- Detection patterns ---
# Maps package names, Docker images, and env vars to technology keys.
# Replaces the hardcoded mappings in setup-team step 5a.
detection:
  pip:
    # Databases
    pymongo: mongodb
    motor: mongodb
    psycopg2: postgresql
    psycopg2-binary: postgresql
    redis: redis
    boto3: aws
    # ... plus 20+ more pip mappings
  npm:
    mongoose: mongodb
    mongodb: mongodb
    pg: postgresql
    ioredis: redis
    redis: redis
    aws-sdk: aws
    "@aws-sdk/client-s3": aws
    # ... plus 15+ more npm mappings
  docker:
    "mongo:*": mongodb
    "postgres:*": postgresql
    "redis:*": redis
    "rabbitmq:*": rabbitmq
    # ... plus 4 more docker mappings
  env:
    "MONGO_URI=*": mongodb
    "REDIS_URL=*": redis
    "REDIS_HOST=*": redis
    "AWS_REGION=*": aws
    # ... plus 14 more env mappings
  go:
    go.mongodb.org/mongo-driver: mongodb
    github.com/lib/pq: postgresql
    github.com/go-redis/redis: redis
    github.com/aws/aws-sdk-go-v2: aws
    # ... plus 8 more go mappings
  gem:
    pg: postgresql
    redis: redis
    aws-sdk: aws
    # ... plus 7 more gem mappings
  cargo:
    redis: redis
    aws-sdk-s3: aws
    diesel: postgresql
    # ... plus 6 more cargo mappings
  # Full file has 116 detection patterns across 7 ecosystems

# --- Technology manifest ---
# Every technology with a registry file is listed here.
technologies:
  # Databases
  mongodb:
    file: mongodb.yaml
    display_name: MongoDB
  postgresql:
    file: postgresql.yaml
    display_name: PostgreSQL
  mysql:
    file: mysql.yaml
    display_name: MySQL
  elasticsearch:
    file: elasticsearch.yaml
    display_name: Elasticsearch
  sqlite:
    file: sqlite.yaml
    display_name: SQLite
  redis:
    file: redis.yaml
    display_name: Redis
  # Cloud platforms
  aws:
    file: aws.yaml
    display_name: Amazon Web Services
  azure:
    file: azure.yaml
    display_name: Microsoft Azure
  gcp:
    file: gcp.yaml
    display_name: Google Cloud Platform
  # ... plus 22 more technologies (31 total)
  # Full manifest covers: messaging, Python/JS frameworks, language
  # ecosystems, DevOps/infrastructure, and services
```

### Index fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | Yes | Schema version. Consumers check this and warn/fail if newer than what they understand. Bumped only for breaking changes. |
| `staleness_threshold_days` | integer | Yes | Number of days after which an entry's `verified_date` is considered stale. Default: 180. |
| `aliases` | map[string, string] | Yes | Maps informal names to canonical technology keys. Values must exist in the `technologies` manifest. |
| `detection` | map[string, map[string, string]] | Yes | Outer key is ecosystem (`pip`, `npm`, `docker`, `env`). Inner key is the package/image/pattern. Value is the canonical technology key. |
| `technologies` | map[string, object] | Yes | Manifest of available technology files. Key is the canonical technology name. |
| `technologies.*.file` | string | Yes | Filename relative to the registry directory. |
| `technologies.*.display_name` | string | Yes | Human-readable technology name for display in reports. |

## Technology File Structure

Each technology file contains everything needed to generate the three-section discovery report.

### Full example: `mongodb.yaml`

```yaml
# MongoDB — Curated technology registry entry
# Covers: MCP server, Claude Code plugin, Python/Node drivers, architecture gaps

display_name: MongoDB
category: database
description: >
  Document database with flexible schema, rich querying, aggregation pipelines,
  and Atlas cloud platform. Widely used for web applications, content management,
  IoT, and real-time analytics.

section_a:
  - name: mongodb-mcp-server
    type: mcp-server-npm
    package: mongodb-mcp-server
    source: https://github.com/mongodb-js/mongodb-mcp-server
    publisher: MongoDB Inc.
    publisher_verified: true
    description: >
      Official MCP server for MongoDB and Atlas — query execution, schema
      inspection, index management, aggregation, Atlas cluster management,
      vector search, performance advisor.
    env:
      - name: MDB_MCP_CONNECTION_STRING
        description: MongoDB connection string
        example: "mongodb://localhost:27017/mydb"
    install_override: |
      npx mongodb-mcp-server@latest --readOnly
      Or install Claude Code plugin: /plugin install mongodb
    verified_date: 2026-04-10

  - name: MongoDB Agent Skills
    type: claude-plugin
    package: mongodb
    source: https://github.com/mongodb/agent-skills
    publisher: MongoDB Inc.
    publisher_verified: true
    description: >
      Official MongoDB agent skills — schema design, query optimization,
      natural language querying, search/AI, Atlas Streams. 7 skills bundled
      with MCP server.
    install_override: |
      /plugin marketplace add mongodb/agent-skills
      /plugin install mongodb@mongodb
    verified_date: 2026-04-10

section_b:
  - name: pymongo
    package: pymongo
    ecosystem: pip
    source: https://pypi.org/project/pymongo/
    publisher: MongoDB Inc.
    description: Official Python driver for MongoDB with sync and async APIs
    usage: "from pymongo import MongoClient"
    docs: https://www.mongodb.com/docs/languages/python/pymongo-driver/current/
    verified_date: 2026-04-10

  - name: mongodb (Node.js)
    package: mongodb
    ecosystem: npm
    source: https://www.npmjs.com/package/mongodb
    publisher: MongoDB Inc.
    description: Official Node.js driver for MongoDB
    usage: 'const { MongoClient } = require("mongodb")'
    docs: https://www.mongodb.com/docs/drivers/node/current/
    verified_date: 2026-04-10

section_c:
  - topic: MongoDB architecture patterns
    slug: mongodb-architecture-advisor
    why: >
      The MCP server + agent skills cover operational tasks and coding patterns,
      but not application-level architecture — repository patterns, connection
      management, schema evolution strategies, testing approaches, sharding key
      selection methodology, and operational readiness.
    agent_would_know: >
      MongoDB application architecture patterns, schema evolution and migration
      strategies, sharding and replication design, testing patterns with
      embedded MongoDB.
    research_scope:
      - Document model design patterns
      - Schema versioning and migration
      - Connection pooling and lifecycle
      - Transaction design (multi-document/distributed)
      - Sharding key selection
      - Testing patterns (test containers/fixtures)
      - Security architecture (field-level encryption/CSFLE)
    create_command: "@pipeline-orchestrator create a mongodb-architecture-advisor agent"
    verified_date: 2026-04-10

our_agents:
  - agent: database-architect
    plugin: sdlc-team-common
    relevance: >
      Schema design, query optimization, index strategy for MongoDB collections.
  - agent: backend-architect
    plugin: sdlc-team-fullstack
    relevance: >
      Application-layer patterns for MongoDB integration (connection pooling,
      retry logic, transactions).

trusted_sources:
  - url: https://github.com/mongodb
    type: github-org
  - url: https://github.com/mongodb-js
    type: github-org
  - url: https://www.npmjs.com/~mongodb
    type: npm-scope
  - url: https://pypi.org/user/mongodb/
    type: pypi-publisher
```

### Full example: `redis.yaml`

```yaml
# Redis — Curated technology registry entry
# Covers: MCP server, Claude Code plugin, Python/Node clients, caching architecture gaps

display_name: Redis
category: cache
description: >
  In-memory data store used as cache, message broker, and real-time database.
  Supports strings, hashes, lists, sets, sorted sets, streams, JSON documents,
  and vector search. Widely used for caching, session management, rate limiting,
  and pub/sub messaging.

section_a:
  - name: redis-mcp-server
    type: mcp-server-pip
    package: redis-mcp-server
    source: https://github.com/redis/mcp-redis
    publisher: Redis Inc.
    publisher_verified: true
    description: >
      Official MCP server for Redis — string/hash/list/set/sorted-set/stream/
      pub-sub operations, JSON documents, vector search, index management,
      server info.
    env:
      - name: REDIS_HOST
        description: Redis server hostname
        example: "127.0.0.1"
      - name: REDIS_PORT
        description: Redis server port
        example: "6379"
      - name: REDIS_PWD
        description: Redis password
      - name: REDIS_SSL
        description: Enable TLS connection
        example: "False"
      - name: REDIS_CLUSTER_MODE
        description: Enable cluster mode
        example: "False"
    install_override: |
      uvx --from redis-mcp-server@latest redis-mcp-server --url redis://localhost:6379/0
    verified_date: 2026-04-10

  - name: Redis Agent Skills
    type: claude-plugin
    package: redis-development
    source: https://github.com/redis/agent-skills
    publisher: Redis Inc.
    publisher_verified: true
    description: >
      Official Redis agent skills — data structure patterns, caching, rate
      limiting, vector search, anti-pattern guardrails, production defaults.
      Knowledge injection, not tools.
    install_override: |
      /plugin marketplace add redis/agent-skills
      /plugin install redis-development@redis
    verified_date: 2026-04-10

section_b:
  - name: redis-py
    package: redis
    ecosystem: pip
    source: https://pypi.org/project/redis/
    publisher: "Redis Inc. (PyPI: RedisLabs)"
    description: Official Python client for Redis
    usage: "import redis"
    docs: https://redis.io/docs/latest/develop/clients/redis-py/
    verified_date: 2026-04-10

  - name: node-redis
    package: redis
    ecosystem: npm
    source: https://www.npmjs.com/package/redis
    publisher: "Redis Inc. (@redis scope)"
    description: >
      Official Node.js client for Redis (recommended over ioredis for new
      projects)
    usage: 'import { createClient } from "redis"'
    docs: https://redis.io/docs/latest/develop/clients/nodejs/
    verified_date: 2026-04-10

section_c:
  - topic: Redis caching architecture patterns
    slug: redis-caching-architect
    why: >
      The MCP server provides data operations and the agent skill teaches correct
      Redis patterns, but neither addresses system-level caching architecture —
      invalidation strategies, TTL policy design, cache stampede prevention,
      multi-tier caching, or cache key design conventions.
    agent_would_know: >
      Cache invalidation patterns (cache-aside, write-through, write-behind),
      TTL policy design, stampede prevention, multi-tier caching, Redis Streams
      for event-driven architectures.
    research_scope:
      - Cache invalidation patterns
      - TTL policy design
      - Cache stampede prevention (locking/probabilistic early expiration)
      - Multi-tier caching (L1 in-process / L2 Redis / L3 persistent)
      - Cache warming strategies
      - Monitoring cache hit ratios and eviction rates
    create_command: "@pipeline-orchestrator create a redis-caching-architect agent"
    verified_date: 2026-04-10

our_agents:
  - agent: database-architect
    plugin: sdlc-team-common
    relevance: >
      Cache layer design, data structure selection, persistence vs pure-cache
      trade-offs.
  - agent: performance-engineer
    plugin: sdlc-team-common
    relevance: >
      Cache hit ratio analysis, latency profiling, connection pool tuning.

trusted_sources:
  - url: https://github.com/redis
    type: github-org
  - url: https://www.npmjs.com/~redis
    type: npm-scope
  - url: https://pypi.org/user/RedisLabs/
    type: pypi-publisher
  - url: https://redis.io/docs/
    type: vendor-docs
```

### Full example: `aws.yaml`

```yaml
# Amazon Web Services — Curated technology registry entry
# Covers: Official MCP servers (curated top 8 of 84+), SDKs, architecture gaps
#
# Full AWS MCP server catalog (84+ servers):
#   https://awslabs.github.io/mcp/
# All servers follow the pattern: uvx awslabs.<name>@latest

display_name: Amazon Web Services
category: cloud
description: >
  Comprehensive cloud platform with 200+ services spanning compute, storage,
  databases, networking, machine learning, analytics, security, and developer
  tools. The dominant public cloud provider by market share.

# NOTE: AWS publishes 84+ official MCP servers at https://awslabs.github.io/mcp/
# The section below curates the most commonly needed ones. Consult the full
# catalog for specialized services (e.g., Bedrock, SageMaker, Aurora DSQL,
# CodePipeline, Neptune, Valkey, etc.).
section_a:
  - name: AWS Documentation MCP Server
    type: mcp-server-pip
    package: awslabs.aws-documentation-mcp-server
    source: https://pypi.org/project/awslabs.aws-documentation-mcp-server/
    publisher: Amazon Web Services
    publisher_verified: true
    description: >
      Fetch AWS docs as markdown, search documentation, get recommendations.
      No AWS credentials needed.
    install_override: "uvx awslabs.aws-documentation-mcp-server@latest"
    verified_date: 2026-04-10

  - name: AWS API MCP Server
    type: mcp-server-pip
    package: awslabs.aws-api-mcp-server
    source: https://pypi.org/project/awslabs.aws-api-mcp-server/
    publisher: Amazon Web Services
    publisher_verified: true
    description: >
      Interact with AWS services via CLI commands with security controls.
    env:
      - name: AWS_REGION
        description: AWS region for API calls
        example: "us-east-1"
      - name: AWS_API_MCP_PROFILE_NAME
        description: AWS CLI profile name
        example: "default"
    install_override: "uvx awslabs.aws-api-mcp-server@latest"
    verified_date: 2026-04-10

  - name: AWS IaC MCP Server
    type: mcp-server-pip
    package: awslabs.aws-iac-mcp-server
    source: https://pypi.org/project/awslabs.aws-iac-mcp-server/
    publisher: Amazon Web Services
    publisher_verified: true
    description: >
      CloudFormation/CDK validation, compliance checking, deployment
      troubleshooting. Supersedes cdk/cfn/ccapi servers.
    env:
      - name: AWS_PROFILE
        description: AWS CLI profile name
    install_override: "uvx awslabs.aws-iac-mcp-server@latest"
    verified_date: 2026-04-10

  - name: AWS Serverless MCP Server
    type: mcp-server-pip
    package: awslabs.aws-serverless-mcp-server
    source: https://pypi.org/project/awslabs.aws-serverless-mcp-server/
    publisher: Amazon Web Services
    publisher_verified: true
    description: >
      Lambda, DynamoDB, API Gateway, ACM, Route 53 — init, deploy, monitor,
      troubleshoot.
    env:
      - name: AWS_PROFILE
        description: AWS CLI profile name
      - name: AWS_REGION
        description: AWS region for API calls
    install_override: "uvx awslabs.aws-serverless-mcp-server@latest"
    verified_date: 2026-04-10

  - name: AWS Billing and Cost Management MCP Server
    type: mcp-server-pip
    package: awslabs.billing-cost-management-mcp-server
    source: https://pypi.org/project/awslabs.billing-cost-management-mcp-server/
    publisher: Amazon Web Services
    publisher_verified: true
    description: >
      Cost Explorer, Cost Optimization Hub, Savings Plans, Budgets, S3 Storage
      Lens, Cost Anomaly Detection.
    env:
      - name: AWS_PROFILE
        description: AWS CLI profile name
      - name: AWS_REGION
        description: AWS region for API calls
    install_override: "uvx awslabs.billing-cost-management-mcp-server@latest"
    verified_date: 2026-04-10

  - name: Amazon CloudWatch MCP Server
    type: mcp-server-pip
    package: awslabs.cloudwatch-mcp-server
    source: https://pypi.org/project/awslabs.cloudwatch-mcp-server/
    publisher: Amazon Web Services
    publisher_verified: true
    description: >
      AI-powered root cause analysis using CloudWatch metrics, alarms, and logs.
    env:
      - name: AWS_PROFILE
        description: AWS CLI profile name
    install_override: "uvx awslabs.cloudwatch-mcp-server@latest"
    verified_date: 2026-04-10

  - name: IAM MCP Server
    type: mcp-server-pip
    package: awslabs.iam-mcp-server
    source: https://pypi.org/project/awslabs.iam-mcp-server/
    publisher: Amazon Web Services
    publisher_verified: true
    description: >
      IAM users, roles, groups, policies, access keys with security simulation.
    env:
      - name: AWS_PROFILE
        description: AWS CLI profile name
      - name: AWS_REGION
        description: AWS region for API calls
    install_override: "uvx awslabs.iam-mcp-server@latest"
    verified_date: 2026-04-10

  - name: Amazon EKS MCP Server
    type: mcp-server-pip
    package: awslabs.eks-mcp-server
    source: https://pypi.org/project/awslabs.eks-mcp-server/
    publisher: Amazon Web Services
    publisher_verified: true
    description: >
      EKS cluster management and application deployment.
    env:
      - name: AWS_PROFILE
        description: AWS CLI profile name
      - name: AWS_REGION
        description: AWS region for API calls
    install_override: "uvx awslabs.eks-mcp-server@latest"
    verified_date: 2026-04-10

section_b:
  - name: boto3
    package: boto3
    ecosystem: pip
    source: https://pypi.org/project/boto3/
    publisher: Amazon Web Services
    description: Official AWS SDK for Python
    usage: "import boto3"
    docs: https://aws.amazon.com/sdk-for-python/
    verified_date: 2026-04-10

  - name: AWS SDK v3 (JavaScript)
    package: "@aws-sdk/client-s3"
    ecosystem: npm
    source: https://www.npmjs.com/package/@aws-sdk/client-s3
    publisher: Amazon Web Services
    description: >
      Official AWS SDK v3 for JavaScript (modular per-service packages).
      v2 is end-of-support.
    usage: 'import { S3Client } from "@aws-sdk/client-s3"'
    docs: https://docs.aws.amazon.com/AWSJavaScriptSDK/v3/latest/
    verified_date: 2026-04-10

section_c:
  - topic: AWS multi-account and organizations strategy
    slug: aws-organizations-expert
    why: >
      No MCP server addresses AWS Organizations, Control Tower, Service Control
      Policies, or multi-account landing zone design.
    agent_would_know: >
      Multi-account strategy, landing zone patterns, SCP design, Organization
      Unit hierarchy.
    research_scope:
      - AWS Organizations best practices
      - Control Tower landing zones
      - SCP design patterns
      - Cross-account access patterns
      - Consolidated billing optimization
    create_command: "@pipeline-orchestrator create an aws-organizations-expert agent"
    verified_date: 2026-04-10

  - topic: AWS application architecture patterns
    slug: aws-application-architect
    why: >
      Existing servers are service-oriented but don't provide opinionated guidance
      on event-driven architectures, CQRS, saga patterns, microservice
      decomposition, or domain-driven design on AWS.
    agent_would_know: >
      Event-driven architecture on AWS, microservice patterns, DDD with AWS
      services, Well-Architected Framework application.
    research_scope:
      - Event-driven architecture patterns (EventBridge/SNS/SQS)
      - Microservice decomposition strategies
      - CQRS and saga patterns on AWS
      - Domain-driven design with AWS services
      - Well-Architected Framework (all 6 pillars)
    create_command: "@pipeline-orchestrator create an aws-application-architect agent"
    verified_date: 2026-04-10

our_agents:
  - agent: solution-architect
    plugin: sdlc-team-common
    relevance: >
      End-to-end AWS solution design, service selection, cost-performance
      trade-off analysis.
  - agent: observability-specialist
    plugin: sdlc-team-common
    relevance: >
      CloudWatch, X-Ray, and OpenTelemetry integration for AWS-hosted
      applications.

trusted_sources:
  - url: https://github.com/aws
    type: github-org
  - url: https://github.com/awslabs
    type: github-org
  - url: https://www.npmjs.com/~aws-sdk
    type: npm-scope
  - url: https://pypi.org/user/awslabs-mcp/
    type: pypi-publisher
  - url: https://awslabs.github.io/mcp/
    type: vendor-docs
```

## Technology File Fields

### Top-level fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `display_name` | string | Yes | Human-readable name for reports. |
| `category` | string | Yes | Grouping: `database`, `cache`, `cloud`, `messaging`, `search`, `payment`, `monitoring`, `auth`, `ci-cd`, `other`. |
| `description` | string | Yes | One-line description of the technology. |
| `section_a` | list | No | Claude Code environment tools. Empty list or omitted if none known. |
| `section_b` | list | No | Project dependency libraries. Empty list or omitted if none known. |
| `section_c` | list | No | Pre-authored gap templates. Empty list or omitted if no gaps identified. |
| `our_agents` | list | No | Framework agent cross-references. Omitted if no agents are relevant. |
| `trusted_sources` | list | Yes | Typed URLs for fallback discovery and freshness verification. |

### Section A entry fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Tool display name. |
| `type` | string | Yes | Category enum: `claude-plugin`, `mcp-server-npm`, `mcp-server-pip`, `mcp-server-binary`, `github-action`, `standalone-cli`. |
| `package` | string | Yes | Installable identifier (npm package, PyPI package, plugin name). |
| `source` | string | Yes | URL to the tool's registry page or repository. |
| `description` | string | Yes | What the tool does. |
| `verified_date` | string | Yes | `YYYY-MM-DD` — when this entry was last verified accurate. |
| `publisher` | string | No | Who publishes the tool. |
| `publisher_verified` | boolean | No | Whether the publisher is the official vendor. Default: false. |
| `env` | list[object] | No | Required environment variables. Each has `name` (string, required), `description` (string, required), `example` (string, optional). |
| `module` | string | No | Python module name for `mcp-server-pip` entries (used in `python -m <module>`). Required when type is `mcp-server-pip` because module names aren't always derivable from package names. |
| `install_override` | string | No | If present, replaces the template-generated install snippet entirely. |

### Section B entry fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Library display name. |
| `package` | string | Yes | Package identifier for the package manager. |
| `ecosystem` | string | Yes | Package manager: `pip`, `npm`, `cargo`, `go`, `gem`. |
| `source` | string | Yes | URL to the library's registry page. |
| `description` | string | Yes | What the library does. |
| `verified_date` | string | Yes | `YYYY-MM-DD` — when this entry was last verified accurate. |
| `publisher` | string | No | Who publishes the library. |
| `usage` | string | No | Import statement from the library's README. |
| `docs` | string | No | URL to documentation. |

### Section C entry fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `topic` | string | Yes | Human-readable name of the gap. |
| `slug` | string | Yes | Lowercase, hyphenated identifier. Used in the `create_command` and as a potential agent filename. |
| `why` | string | Yes | What's missing that a custom agent would provide. |
| `agent_would_know` | string | Yes | 1-2 sentence description of the intended expertise. |
| `research_scope` | list[string] | Yes | Topics the research campaign would cover. |
| `create_command` | string | Yes | The pipeline-orchestrator invocation to build this agent. |
| `verified_date` | string | Yes | `YYYY-MM-DD` — when this gap assessment was last verified. |
| `estimated_duration` | string | No | Expected pipeline duration. Default: "2-3 hours". |

### `our_agents` entry fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent` | string | Yes | Agent name (as it appears in the plugin's agents directory). |
| `plugin` | string | Yes | Plugin that provides the agent (e.g., `sdlc-team-fullstack`). Tells setup-team which plugin to recommend. |
| `relevance` | string | Yes | Why this agent matters for this technology. Shown to the user. |

### `trusted_sources` entry fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | Yes | URL to the trusted source. |
| `type` | string | Yes | Source type enum: `github-org`, `npm-scope`, `pypi-publisher`, `vendor-docs`, `other`. Tells the discovery agent how to search this source. |

## Install Template System

Setup-team and pipeline-orchestrator generate install snippets from the `type` and structured fields of each entry. Seven category templates, one per `type`:

### `mcp-server-npm`

Template inputs: `package`, entry `name`, `env[]`

```
Add to .mcp.json:
{
  "mcpServers": {
    "<name>": {
      "command": "npx",
      "args": ["-y", "<package>"],
      "env": {
        "<env.name>": "<env.example or description>"
      }
    }
  }
}
Then restart Claude Code or run /mcp.
```

### `mcp-server-pip`

Template inputs: `package`, `module` (from the entry's `module` field), `env[]`

```
pip install <package>

Add to .mcp.json:
{
  "mcpServers": {
    "<name>": {
      "command": "python",
      "args": ["-m", "<module>"],
      "env": {
        "<env.name>": "<env.example or description>"
      }
    }
  }
}
```

### `mcp-server-binary`

Template inputs: `source`, `name`, `env[]`

```
Download from <source>/releases
Add to .mcp.json with absolute path to the binary.
```

### `claude-plugin`

Template inputs: `package` (plugin name), marketplace owner/repo

```
/plugin marketplace add <owner>/<repo>
/plugin install <plugin-name>@<marketplace-name>
```

### `github-action`

Template inputs: `source`, version tag

```yaml
- name: <description>
  uses: <owner>/<repo>@<version-tag>
  with:
    <input>: <value>
```

### `standalone-cli`

Template inputs: `source`, `name`

```bash
git clone <source> ~/tools/<name>
cd ~/tools/<name>
# Follow README for run instructions
```

### `library-framework` (Section B)

Template inputs: `package`, `ecosystem`

```bash
<pip|npm|cargo add|go get> install <package>
```

### `install_override`

If the `install_override` field is present on any entry, the LLM emits its contents verbatim instead of generating from the template. This handles tools with non-standard install flows.

## Lookup and Fallback Flow

### Detection (replaces hardcoded mappings in setup-team step 5a)

```
1. Load _index.yaml
2. For each dependency file (requirements.txt, package.json, etc.):
   a. Identify ecosystem (pip, npm, docker, env)
   b. For each package/image/var in that file:
      - Look up in detection[ecosystem] -> technology key
      - If found -> add to detected technologies set
3. Present detected technologies to user (same as current step 5b)
```

### Recommendation (replaces web search in setup-team step 5c)

```
1. For each detected technology:
   a. Normalize via aliases map -> canonical key
   b. Check technologies manifest -> has a file?
      YES -> load <technology>.yaml -> emit sections A/B/C from registry
      NO  -> fall back to web search (current step 5c behavior)
```

### Pipeline-orchestrator (replaces Phase 0 steps 1-6)

```
1. Extract target technology from user request
2. Load _index.yaml, normalize via aliases
3. Technology in registry?
   YES -> load file, emit three-section report from registry data
   NO  -> execute Phase 0 steps 1-9 as today (web search)
4. Steps 7-9 (classification, gap assessment, report) unchanged
   -- registry pre-classifies, report format is identical
```

### Key property

The registry is additive. Both consumers already work without it. The registry is a fast path that short-circuits web search. If the registry directory is missing or empty, everything falls back to current behavior.

## Validation Rules

A future `check-technology-registry.py` validator (sub-feature 8) enforces these rules:

| # | Rule | Scope | Check |
|---|------|-------|-------|
| 1 | Required fields present | Per entry | Section A/B/C entries have all required fields per the field tables above. |
| 2 | Type enum valid | Section A | `type` is one of `claude-plugin`, `mcp-server-npm`, `mcp-server-pip`, `mcp-server-binary`, `github-action`, `standalone-cli`. |
| 3 | Ecosystem enum valid | Section B | `ecosystem` is one of `pip`, `npm`, `cargo`, `go`, `gem`. |
| 4 | Trusted source type valid | trusted_sources | `type` is one of `github-org`, `npm-scope`, `pypi-publisher`, `vendor-docs`, `other`. |
| 5 | Dates parseable | Per entry | `verified_date` is valid `YYYY-MM-DD`. |
| 6 | Slug format valid | Section C | `slug` is lowercase, hyphenated, no spaces, no special characters. |
| 7 | Index-file consistency | Registry | Every file in the manifest exists on disk; every `.yaml` file (except `_index.yaml`) is in the manifest. |
| 8 | Alias targets valid | Index | Every alias value maps to a key in the technologies manifest. |
| 9 | Detection targets valid | Index | Every detection value maps to a key in the technologies manifest. |
| 10 | No duplicate detection keys | Index | No package name appears twice in the same ecosystem. |

## Schema Evolution

The `version` field in `_index.yaml` tracks the schema version.

- **Non-breaking changes** (new optional fields, new enum values): version stays the same. Consumers ignore fields they don't understand.
- **Breaking changes** (required field additions, structural reorganization, field renames): bump the version. Consumers check `version` and warn or fail if it's newer than what they support.

## Design Decisions Log

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Split YAML files, one per technology | Scales beyond 30 entries, clean git diffs, context-efficient for LLM consumers (load only what you need). |
| 2 | YAML over JSON | ~20-30% fewer tokens, more readable for LLMs and humans, parseable by Python (`yaml.safe_load`), consistent with existing project patterns. |
| 3 | Index file with detection patterns | Single file load for tech-stack scanning. Detection is data-driven — adding a technology to the registry automatically teaches setup-team to detect it. |
| 4 | Separate alias lookup table | Aliases are a cross-cutting concern about how you find an entry, not about the entry itself. Easier to maintain without touching technology files. |
| 5 | Pre-authored Section C gap templates | Curated, high-quality gap descriptions. Avoids web-search latency. The whole point of the registry is to front-load this work. |
| 6 | Hybrid install snippets (template + override) | Templates cover 90%+ of entries (7 categories with well-defined patterns). `install_override` handles edge cases without forcing every entry to carry verbose snippets. |
| 7 | Per-technology cross-references with context | Agents are relevant to the technology as a whole, not a specific third-party tool. `plugin` field tells setup-team what to recommend; `relevance` tells the user why. |
| 8 | Typed trusted sources | `type` field tells the discovery agent how to search the source (GitHub org -> search repos, npm scope -> search packages). Serves both fallback discovery and freshness verification. |
| 9 | Per-entry verified dates | Verification happens at the tool level. A technology-level date would either be inaccurate or force all-or-nothing sweeps. |
| 10 | Registry-level staleness threshold | One configurable field. Maintenance process (sub-feature 8) can tune it. Individual entries don't need their own threshold. |
| 11 | Registry is additive, not breaking | Both consumers already work without it. Missing registry = current web-search behavior. No migration needed. |

## What Changes in Consumers

### setup-team (skill)

| Step | Current behavior | With registry |
|------|-----------------|---------------|
| 5a (detection) | Hardcoded package-to-technology mappings | Read `_index.yaml` detection map |
| 5c (discovery) | Web search per technology | Load technology YAML file; web search only for technologies not in registry |
| 5c.1 (install snippets) | Generated from web search results | Generated from registry fields + category templates |
| 5d, 5e | Unchanged | Unchanged |

### pipeline-orchestrator (agent)

| Phase | Current behavior | With registry |
|-------|-----------------|---------------|
| Phase 0 steps 1-6 | Web search, registry checks, vendor GitHub | Registry lookup for known technologies |
| Phase 0 steps 7-9 | Classification, gap assessment, report | Unchanged — registry pre-classifies, report format identical |

## Downstream Sub-features

| Sub-feature | Issue | Dependency on this schema |
|-------------|-------|--------------------------|
| 4: Populate registry | #146 | Creates `_index.yaml` + 20-30 technology files using this schema |
| 5: Wire into setup-team | #147 | Modifies skill to read `_index.yaml` and technology files |
| 6: Wire into pipeline-orchestrator | #148 | Modifies agent to check registry before web search |
| 7: Cross-reference our plugins | #149 | Populates `our_agents` field across technology files |
| 8: Maintenance strategy | #150 | Defines process for updating `verified_date`, adding entries, staleness checks |
