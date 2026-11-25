
# GridGuard DevSecOps Security Baseline

## 1. Purpose

This document defines the initial DevSecOps security baseline
for the GridGuard Smart Grid Asset Platform.

The baseline introduces automated code checks, secret detection,
container vulnerability scanning, and secure local development
infrastructure.

## 2. Development Infrastructure

The development environment is defined in:

- `docker-compose.dev.yml`

Services:

| Service | Purpose |
|---|---|
| PostgreSQL/PostGIS | Relational database and geospatial data |
| Redis | Cache and token blacklist storage |
| EMQX | MQTT messaging broker |
| Backend | FastAPI application |
| AI Service | Not available until its implementation is provided |

Infrastructure services use health checks where configured.
Database and Redis data are persisted using Docker volumes.

Development ports are bound to `127.0.0.1` to avoid exposing
services on all host network interfaces.

## 3. Python Security and Code Quality

Pre-commit checks are configured in `.pre-commit-config.yaml`.

Tools:

- Ruff: Python linting and formatting checks.
- Black: Python code formatting.
- Gitleaks: Secret detection.

Install and configure:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## 4. CI Security Scanning

GitHub Actions workflow:

`.github/workflows/security_baseline.yml`

The workflow runs:

- Bandit against `backend/src`.
- Trivy against `python:3.12-slim`.
- Trivy against `node:18-alpine`.

High severity Bandit findings fail the security job.
High and Critical Trivy findings fail the image scan job.

Pull requests targeting `main` trigger the workflow.

## 5. Container Scanning

The local scanning script is:

`scripts/scan_containers.sh`

Requirements:

- Docker
- Trivy
- Internet access to retrieve image metadata and vulnerability databases

Run:

```bash
bash scripts/scan_containers.sh
```

The script returns a non-zero exit code when a blocking
vulnerability is detected or a scan fails.

## 6. Secrets Management

- Never commit `.env` files.
- Use `.env.example` only for placeholder configuration.
- Do not hardcode production credentials in source code.
- Use GitHub Secrets for sensitive CI/CD configuration when needed.
- Rotate any secret accidentally exposed in Git history.

## 7. Vulnerability Management

- Review all High and Critical container findings.
- Update vulnerable base images and dependencies.
- Re-run security scans after remediation.
- Document accepted risks and their justification.
- Do not merge changes while blocking security checks fail.

## 8. Current Limitations

- The AI service implementation is not currently available
  in the repository.
- Container scans depend on registry and vulnerability database
  availability.
- The baseline is intended for development and CI validation,
  not as a complete production security architecture.
- Production deployment requires additional hardening,
  secret management, access control, and monitoring.

## 9. Verification Evidence

Record the actual results of:

- Docker Compose configuration validation.
- Backend image build.
- Infrastructure service health checks.
- Backend health endpoint.
- Pre-commit checks.
- Bandit workflow.
- Trivy image scans.

Do not mark a check as passed until it has been executed.

## 10. Initial Vulnerability Scan Results

Initial Trivy scans were executed after pulling the latest
available images for the configured tags.

| Image | High | Critical | Result |
|---|---:|---:|---|
| python:3.12-slim | 53 | 0 | BLOCKED |
| node:18-alpine | See per-target results below | See per-target results below | BLOCKED |

Node image scan reported separate target summaries:
- Alpine OS target: 24 findings (22 High, 2 Critical).
- Node package target: 22 findings (21 High, 1 Critical).

The target summaries are reported separately and must not be
treated as a deduplicated image-wide total.

Trivy also warned that Alpine 3.21.3 is no longer supported.

These findings are not marked as passed. The configured
security gate correctly returns a non-zero exit code when
High or Critical vulnerabilities are detected.

Remediation is required before the images can pass the
security baseline.
