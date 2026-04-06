# EventFlow

Real-time event analytics platform for e-commerce. Ingests customer events
via Apache Kafka, stores in MongoDB for flexible schema, processes with
Python workers, serves dashboards via React frontend backed by a FastAPI
REST API. Uses Redis for caching and session management. Deployed to AWS
with Terraform. Business reporting exported as PowerPoint presentations
for stakeholder reviews.

## Tech Stack

- **Backend**: Python 3.12, FastAPI, Celery workers
- **Frontend**: React 18, TypeScript, Tailwind CSS
- **Database**: MongoDB Atlas (primary store), Redis (cache + sessions)
- **Messaging**: Apache Kafka (event streaming)
- **Infrastructure**: AWS (ECS, S3, CloudWatch), Terraform
- **Reporting**: Python-pptx for automated PowerPoint generation
- **CI/CD**: GitHub Actions
- **Monitoring**: Grafana + Prometheus

## Architecture

Events flow from client SDKs → Kafka topics → Python Celery workers →
MongoDB collections. The FastAPI backend serves both the React dashboard
and the REST API for external integrations. Redis handles session state
and hot-path caching. Terraform manages all AWS infrastructure as code.

Weekly stakeholder reports are generated automatically as PowerPoint
presentations from MongoDB aggregation queries.
