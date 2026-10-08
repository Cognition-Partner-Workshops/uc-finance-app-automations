# Target Architecture Constraints

This document describes the **target state** architecture that TraderX should be migrated to. Nothing described here is currently implemented. This serves as a requirements and constraints document for a future migration project.

---

## 1. Isolated Deployments

TraderX serves one customer per installation: each customer runs its own deployment with no shared runtime state between deployments.

- Each deployment gets its own set of running service instances
- No shared mutable in-memory state between service instances (no process-global `_runtime_state`)
- Configuration — including business rules such as max accounts, allowed sides, auto-settle — is injected per deployment via environment variables or secrets, not read from a shared config module
- A failure in one deployment must not affect any other deployment

---

## 2. Dedicated Database per Deployment

Each deployment must have its own database or database schema. No database is shared between deployments.

- **Option A: Database-per-deployment** — each deployment gets a dedicated database instance (e.g., separate PostgreSQL or Azure SQL databases)
- **Option B: Schema-per-deployment** — each deployment gets a dedicated schema within a shared database cluster
- Isolation is enforced at the infrastructure level, not by filtering in application code
- Database credentials are deployment-specific and injected via environment variables or secrets management
- Cross-deployment queries are impossible by design

---

## 3. Containerized Services

All services must be packaged as Docker containers.

- Each service has its own `Dockerfile` with a minimal base image
- Images are tagged with semantic version and commit SHA
- Images are stored in a private container registry (e.g., AWS ECR, Azure ACR)
- Containers run as non-root users
- Health check endpoints (`/health`) are defined in Docker `HEALTHCHECK` instructions
- No host-level dependencies — all runtime dependencies are baked into the container image

---

## 4. Kubernetes Deployable

The application must be deployable to a managed Kubernetes cluster.

- Target clusters: AWS EKS or Azure AKS
- Each service has its own Kubernetes `Deployment`, `Service`, and `HorizontalPodAutoscaler`
- Readiness and liveness probes configured for all services
- Resource requests and limits defined for all containers
- Namespaces used for environment isolation (e.g., `traderx-dev`, `traderx-staging`, `traderx-prod`)
- Secrets managed via Kubernetes Secrets or an external secrets manager (e.g., AWS Secrets Manager, Azure Key Vault)
- ConfigMaps used for non-sensitive configuration

---

## 5. GitHub Actions CI/CD

An automated CI/CD pipeline must be in place using GitHub Actions.

- **CI (on every PR)**:
  - Lint and type-check all source code
  - Run unit tests with coverage thresholds
  - Run integration tests against a test database
  - Build Docker images
  - Static security scanning (e.g., Trivy for container images, CodeQL for source)
- **CD (on merge to main)**:
  - Build and push Docker images to the container registry
  - Deploy to staging environment automatically
  - Run smoke tests against staging
  - Manual approval gate for production deployment
  - Deploy to production with rolling update strategy
- **Environment promotion**: `dev` -> `staging` -> `production`

---

## 6. Terraform for Azure/AWS Infrastructure

All infrastructure must be defined as code using Terraform.

- VPC/VNet, subnets, security groups
- Kubernetes cluster (EKS or AKS)
- Database instances (RDS/Azure SQL) — one per deployment
- Container registry (ECR/ACR)
- Load balancers and DNS records
- Secrets manager configuration
- Monitoring and alerting infrastructure
- State stored in a remote backend (S3/Azure Blob) with state locking
- Separate Terraform workspaces or state files per environment

---

## 7. Service Boundaries Aligned with Domain Ownership

The monolith must be decomposed into services aligned with business domains.

| Service | Domain | Responsibilities |
|---|---|---|
| **Account Service** | Accounts | Account CRUD, account user management, account validation |
| **Trading Service** | Trading | Trade submission, trade validation, trade state machine |
| **Position Service** | Positions | Position tracking, position queries, position recalculation |
| **Reference Data Service** | Reference Data | Stock ticker lookup, S&P 500 data |
| **People Service** | People | Person directory, person validation |

Each service:
- Owns its own data store (no shared database)
- Has a well-defined API contract (OpenAPI/Swagger)
- Can be developed, deployed, and scaled independently
- Has its own CI/CD pipeline
- Has its own team ownership

---

## 8. No Cross-Service Database Access

Services must not query each other's databases. All inter-service communication must go through APIs.

- The Trade Service validates accounts by calling the Account Service API (not by querying the accounts table)
- The Trade Service validates securities by calling the Reference Data Service API (not by loading a CSV)
- Position updates are triggered by events (not by direct database writes from the trade processor)
- Reporting and aggregation queries that span multiple domains use an API composition pattern or a dedicated read model
- No circular dependencies between services — dependency graph must be a DAG

---

## 9. API Gateway for Routing

A central API gateway must handle all ingress traffic.

- Routes requests to the appropriate service based on path prefix
- Handles TLS termination
- Enforces authentication and authorization (e.g., JWT validation)
- Rate limiting per client
- Request/response logging
- CORS configuration centralized at the gateway level
- Candidate technologies: AWS API Gateway, Azure API Management, Kong, or Kubernetes Ingress with nginx

---

## 10. Observability

The system must have comprehensive observability covering logs, metrics, and traces.

### Structured Logging
- All services emit structured JSON logs
- Logs include correlation IDs and request IDs
- Logs are aggregated in a central logging platform (e.g., CloudWatch, Azure Monitor, ELK)

### Metrics (Prometheus)
- Each service exposes a `/metrics` endpoint in Prometheus format
- Key metrics: request rate, error rate, latency percentiles, active connections
- Business metrics: trades per second, position updates per second, active accounts
- Prometheus scrapes all service metrics; Grafana dashboards for visualization
- Alerting rules defined for SLO violations

### Distributed Tracing (OpenTelemetry)
- All services instrumented with OpenTelemetry SDKs
- Traces propagated across service boundaries via HTTP headers
- Trace data exported to a tracing backend (e.g., Jaeger, AWS X-Ray, Azure Application Insights)
- End-to-end trace from trade submission through processing to position update

---

## Summary of Constraints

| Constraint | Current State | Target State |
|---|---|---|
| Deployment isolation | Single process and SQLite file on one host | Dedicated runtime and database per deployment |
| Deployment | Manual `deploy.sh` | Kubernetes (EKS/AKS) with Terraform |
| CI/CD | None | GitHub Actions with automated pipeline |
| Service architecture | Single monolith (1 process) | 5+ independent services |
| Database access | Cross-domain queries, shared tables | Service-owned databases, API communication |
| Routing | Direct FastAPI routes | API gateway with auth and rate limiting |
| Observability | Basic Python logging | Structured logs, Prometheus metrics, OpenTelemetry traces |
| Containerization | None | Docker containers for all services |
| Infrastructure | Manual setup | Terraform IaC |
