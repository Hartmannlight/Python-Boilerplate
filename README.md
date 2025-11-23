# Python Boilerplate – Sync & Async Service Template

This boilerplate provides a clean, minimal, and observable foundation for Python services.
It supports **two execution models**:

1. **Synchronous services** – ideal for cron-style workers, polling loops, data processors, database/HTTP jobs.
2. **Asynchronous services** – ideal for high-concurrency or event-driven systems such as Discord bots, WebSocket clients, async HTTP services, etc.

Both models share the same configuration system, logging baseline, metrics, health checks, Docker setup, and CI pipeline.

---

# 1. Features

### Observability
- Unified **JSON logging** (single line, includes timestamp, instance, env, service, error fields, etc.).
- **Prometheus metrics** endpoint (`/metrics`) with baseline metrics:
  - `app_up`
  - `app_iterations_total`
  - `app_last_iteration_timestamp_seconds`
  - `app_build_info`
- Built-in **health check** (`app-health`) that validates metrics freshness.
- Lifecycle logging for startup, shutdown, and crashes.

### Config
- Load config from:
  - environment variables
  - optional YAML file (`config.yml`)
- Config precedence: **env > YAML > defaults**
- All values are validated and normalized (bool, int, float).

### Sync & Async Runtime Models
- **Sync service**: classic blocking loop (`service_sync.Service`)
- **Async service**: asyncio-based loop (`service_async.AsyncService`)
- Both controlled through separate entry points.

### Development & CI
- Poetry environment
- Pre-commit (mypy, ruff, YAML/TOML/JSON checks)
- GitHub Actions: lint + test + docker build + smoke test
- Dockerfile with build cache support

---

# 2. When to use Sync vs. Async?

### Use **sync** when:
- You have a simple worker loop ("do something every X seconds").
- You use blocking libraries (e.g. `requests`, psycopg2) and don’t need concurrency.
- You want minimal complexity.

### Use **async** when:
- You build a Discord bot, FastAPI app, WebSocket client, proxy, or any event-driven system.
- You need to run many I/O operations concurrently.
- You already rely on async libraries (`aiohttp`, `httpx.AsyncClient`, `asyncpg`, etc.).

The boilerplate lets you choose the right model per project without changing the infrastructure.

---

# 3. Directory Structure

```

src/app
│
├── config.py          # unified configuration loading
├── logging_setup.py   # JSON logging baseline
├── metrics.py         # Prometheus metrics
├── health.py          # CLI health endpoint
│
├── service_sync.py    # synchronous service loop
├── service_async.py   # asynchronous service loop
│
├── main_sync.py       # entry point for sync workers
└── main_async.py      # entry point for async workers

```

---

# 4. Running a Synchronous Service

Sync entry point is installed as:

```

poetry run app-sync

````

or via Docker:

```yaml
command: ["poetry", "run", "app-sync"]
````

The sync service uses a classic blocking loop:

```python
from app.service_sync import Service

service = Service(config)
service.start()
```

---

# 5. Running an Asynchronous Service

Async entry point is:

```
poetry run app-async
```

or via Docker:

```yaml
command: ["poetry", "run", "app-async"]
```

The async service runs on asyncio:

```python
from app.service_async import AsyncService

service = AsyncService(config)
await service.start()
```

### Perfect for:

* Discord bots
* Async HTTP workers
* Websocket clients
* High-concurrency I/O tasks

---

# 6. Health Check

Every container can be validated via:

```
poetry run app-health
```

Exit codes:

* `0` → healthy
* `1` → unhealthy

This is the recommended Docker healthcheck command.

---

# 7. Metrics

If enabled (`metrics_enabled=true`), the service exposes:

```
http://localhost:<metrics_port>/metrics
```

Baseline metrics give you:

* uptime
* iteration frequency
* last-loop freshness
* deployment info (version, commit, env)

---

# 8. Logging

All logs follow the unified JSON format:

```json
{
  "ts": "...",
  "level": "info",
  "service": "python-service",
  "logger": "app.main",
  "instance": "myhost",
  "env": "dev",
  "msg": "Service startup succeeded",
  "event": "startup_success"
}
```

Errors include stack traces automatically.

---

# 9. Configuration

A `.env` file can override or supplement configuration:

```env
APP_SERVICE_NAME=python-service
APP_ENV=dev
APP_LOG_LEVEL=INFO
APP_METRICS_ENABLED=1
APP_METRICS_PORT=8000
APP_LOOP_SLEEP_SECONDS=5.0
```

Optionally load YAML config:

```yaml
service_name: python-service
metrics_enabled: true
metrics_port: 8000
loop_sleep_seconds: 5.0
```

---

# 10. Tests

Run the full suite:

```
poetry run pytest
```

Coverage is preconfigured.

---

# 11. Docker

Build and run:

```
docker build -t python-service .
docker run --rm -p 8000:8000 python-service
```

CI automatically:

* runs tests
* builds/pushes images
* performs smoke tests

---

# 12. Summary

This boilerplate lets you start any kind of Python backend quickly:

* **Sync workers** for polling, simple loops, data processing
* **Async services** for event-driven, high-concurrency environments

Everything else (logging, health, metrics, config, CI, Docker) is unified and ready to use.
