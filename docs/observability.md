# Observability Baseline

Scope: workers, cron jobs, small background services, and home-lab projects.

This baseline exists to make generated and human-written code observable with low friction and high consistency.
The main goal is not "more logs", but faster detection and diagnosis of failures, regressions, and unexpected behavior.

## Goals

- Every service exposes a minimal, consistent observability surface.
- Logs are structured, machine-readable, and useful for diagnosis.
- Metrics make failures and performance regressions visible.
- Health and readiness can be checked automatically.
- Shutdown behavior is predictable and visible.
- Telemetry is flushed before process exit.
- New projects follow the same conventions.
- Agents do not invent observability patterns per project.

## Standard stack

Projects in this boilerplate use:

- Logging: Python `logging` + `structlog`
- Metrics: `prometheus_client`
- Tracing: OpenTelemetry
- Error tracking: `sentry-sdk`

Application code should use the local observability module instead of configuring these tools ad hoc.

## Core rules

- All application logs are single-line structured JSON on stdout.
- Instrument boundaries, not every helper call.
- Metric labels stay low-cardinality.
- Unexpected exceptions are captured once at the handling boundary.
- Do not log secrets or sensitive payloads.
- New endpoints, workers, and scheduled jobs must include baseline instrumentation.
- Runtime configuration comes from environment variables.
- Optional YAML files are for complex domain configuration, not for overriding runtime settings.

## Required log fields

- `ts`
- `level`
- `service`
- `env`
- `msg`
- `event`

Common optional fields:

- `version`
- `commit`
- `instance`
- `logger`
- `request_id`
- `trace_id`
- `span_id`
- `job_name`
- `duration_ms`
- `outcome`

## Required lifecycle events

- `startup_success`
- `shutting_down`
- `shutdown_complete`
- `crashed`

## Metrics baseline

Long-running services expose:

- `app_up`
- `app_info`
- `app_start_time_seconds`
- `last_progress_timestamp_seconds`
- `iterations_total`
- `iteration_duration_seconds`
- `last_success_timestamp_seconds`
- `failures_total`

## Health

This boilerplate includes a CLI health command for non-HTTP services.
It exits with `0` on success, non-zero on failure, and emits structured JSON.
By default it acts as a liveness check based on `app_up`.
For freshness it prefers `last_success_timestamp_seconds`.
If a service does not expose that signal, the health command falls back to `last_progress_timestamp_seconds`.
Failed iterations should still refresh `last_progress_timestamp_seconds`, so "the worker is alive and doing work" is distinguishable from "the worker is stuck".
Freshness is enforced via `APP_HEALTH_MAX_AGE_SECONDS`.
If the metrics endpoint responds with malformed payload, the health command returns a structured unhealthy result instead of crashing.

## Cooperative shutdown

Long-running iterations should be interruptible at sensible checkpoints.
The worker base passes a `stop_event` into `execute_iteration(...)` so concrete services can stop waiting, polling, or batching work when shutdown has been requested.
This is important for containerized deployments where graceful termination windows are finite.

## Project structure

```text
src/python_boilerplate/
├── app.py
├── cli.py
├── config/
│   └── settings.py
├── runtime/
│   └── health.py
├── services/
│   └── worker.py
└── observability/
    ├── __init__.py
    ├── bootstrap.py
    ├── errors.py
    ├── logging.py
    ├── metrics.py
    └── tracing.py
```
