
# Python Service Boilerplate (Observability-Ready)

This boilerplate provides:

- Poetry for dependency management
- FastAPI-based HTTP service (can be replaced)
- JSON logging following an observability baseline
- Prometheus metrics (optional, configurable)
- `/healthz`, `/readyz`, `/metrics` endpoints
- Docker + Docker Compose (prod + dev override)
- GitHub Actions for linting and build
- pre-commit with ruff, mypy, basic hygiene checks
- Basic test structure and coverage configuration

---

## 0. After cloning: quick setup

Run these commands once after cloning:

```bash
git config user.email "hartmannlight@gmail.com"
git config user.name "Nathaniel Hartmann"
git config commit.gpgsign false
```

```bash
# 1) Install dependencies from the existing lock file
poetry install

# 2) Install pre-commit hooks (optional but recommended)
poetry run pre-commit install

# 3) Run tests to verify everything works
poetry run pytest
````

If you change dependencies in `pyproject.toml` later:

```bash
# Regenerate the lock file and install updated deps
poetry lock
poetry install
```

If you want to update libraries to the latest compatible versions:

```bash
# Update all dependencies
poetry update

# Or update specific packages
poetry update fastapi uvicorn prometheus-client
```

---

## 1. Checklist: turning this boilerplate into a real project

Work through these sections in order when you fork/use this template.

### 1.1 Project metadata (`pyproject.toml`)

* [ ] Update `[tool.poetry].name`
* [ ] Update `[tool.poetry].description`
* [ ] Update `[tool.poetry].authors`
* [ ] Update `[tool.poetry].packages` and rename the folder in `src/app` if needed
* [ ] Update `[tool.poetry].scripts` if you change the entrypoint (default is `app.main:main`)
* [ ] Adjust Python version if required
* [ ] Add or remove dependencies (runtime + dev) as needed

---

### 1.2 Service name & configuration

Files involved: `.env.example`, `src/app/config.py`.

* [ ] Set `APP_SERVICE_NAME` in `.env.example` to your service’s canonical name
* [ ] Adjust `APP_ENV` default (`dev`, `stg`, or `prod`)
* [ ] Adjust ports (`APP_HTTP_PORT`, `METRICS_PORT`) as needed
* [ ] Adjust `APP_VERSION` / `APP_COMMIT` defaults (CI can override them)
* [ ] In `config.py`, keep defaults in sync with your `.env` and actual usage
* [ ] Extend `AppConfig` when you introduce new configuration keys (DB URLs, tokens, feature flags)
* [ ] Add new keys to `.env.example` whenever you extend `AppConfig`

---

### 1.3 Docker & docker-compose

Files involved: `Dockerfile`, `docker-compose.yml`, `docker-compose.override.yml`.

* [ ] Set a proper image name in `docker-compose.yml` (e.g. `ghcr.io/<org>/<project>:latest`)
* [ ] Rename the service and `container_name` to something meaningful
* [ ] Adjust port mappings to match your HTTP + metrics ports
* [ ] Update `docker-compose.override.yml` (dev image name, bind mounts, environment overrides)
* [ ] If you change the entrypoint or server, update `CMD` and `EXPOSE` in `Dockerfile`
* [ ] Add any extra OS-level dependencies you need to the `Dockerfile` (apt-get etc.)

---

### 1.4 Observability — Logging

Files involved: `src/app/logging_setup.py`.

* [ ] Verify the JSON log schema matches your needs:

  * `ts`, `level`, `service`, `logger`, `instance`, `env`, `msg`
* [ ] Add structured fields via `extra={...}` when logging:

  * e.g. `request_id`, `event`, `dependency`, `error`
* [ ] Ensure error logs include stack traces and `exception_type` where relevant
* [ ] Adjust the access log filter in `logging_setup.py`:

  * By default, all HTTP access logs for `/metrics` are dropped to avoid polluting Loki with Prometheus scrapes
  * You can add `/healthz` and `/readyz` to the ignore list if you also want to suppress health checks

---

### 1.5 Observability — Metrics

Files involved: `src/app/metrics.py`, `src/app/http.py`.

* [ ] Decide if you want to keep Prometheus metrics

  * If **not**:

    * Remove `prometheus-client` from dependencies
    * Remove the metrics imports and middleware from `http.py`
    * Remove `start_metrics_server` calls from `main.py`
  * If **yes**:

    * Add service-specific counters/gauges/histograms
    * Use `app_dependency_latency_seconds` and `app_dependency_errors_total` to instrument external systems (DB, caches, APIs)
    * Respect label cardinality (no user IDs, tokens, etc.)

---

### 1.6 Observability — Health & readiness

Files involved: `src/app/http.py`.

* [ ] Implement real dependency checks in `/readyz`:

  * example: database ping, cache status, required config loaded
* [ ] Return `503` if any critical dependency is not ready
* [ ] Keep `/healthz` lightweight (process liveness only)

---

### 1.7 Testing & Coverage

Files involved: `tests/`, `pyproject.toml`.

* [ ] Extend `tests/` with real tests for your own endpoints and logic
* [ ] Use coverage to track test completeness:

  * `poetry run coverage run -m pytest`
  * `poetry run coverage report`
* [ ] Adjust coverage configuration in `pyproject.toml` (`tool.coverage.*`) if you add more packages/modules

---

### 1.8 GitHub Actions

Files involved: `.github/workflows/lint.yml`, `.github/workflows/build.yml`.

* [ ] Update Python version in workflows to match `pyproject.toml`
* [ ] Update smoke-test URLs and ports in the build workflow (health, readiness, metrics)
* [ ] Ensure GHCR permissions are set for your repository if you push images
* [ ] Adjust triggers (`branches`, `release` types) to your branching model

---

### 1.9 pre-commit setup

Files involved: `.pre-commit-config.yaml`, `scripts/repo_state_check_gui.py`.

* [ ] Run `poetry run pre-commit install` once locally
* [ ] Decide whether you want the GUI commit confirmation:

  * If **yes**: keep `repo_state_check_gui.py` and its hook
  * If **no**:

    * Remove the `repo-state-check` block from `.pre-commit-config.yaml`
    * Optionally delete `scripts/repo_state_check_gui.py`

---

## 2. File overview

Short description of what each part of the boilerplate is for.

### Root

* `README.md`
  Instructions, checklist, and file overview.

* `.env.example`
  Template for environment variables. Copy to `.env` and adjust for your environment.

* `.gitignore`
  Ignores virtualenvs, caches, build artifacts, logs, and local configuration files.

* `.pre-commit-config.yaml`
  pre-commit hook configuration for formatting, linting, and optional GUI commit checks.

* `Dockerfile`
  Defines how to build the service container image with Poetry and how to run the app.

* `docker-compose.yml`
  Production-like composition:

  * uses a pre-built image
  * wires ports
  * mounts `.env` for configuration

* `docker-compose.override.yml`
  Development overrides:

  * builds from local sources
  * mount `./src` for live code changes
  * overrides environment variables for development

---
