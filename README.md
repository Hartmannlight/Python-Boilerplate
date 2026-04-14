# Python Boilerplate

Ein opinionated Python-Service-Boilerplate mit `uv` und verpflichtender Observability-Baseline.
Es ist in seinem aktuellen Zuschnitt fuer Worker, Cron-Jobs und kleine Hintergrunddienste gedacht, bei denen Logging, Metrics, Tracing, Error-Tracking und Health nicht jedes Mal neu erfunden werden sollen.

## Enthalten

- `uv` fuer Locking, Sync und Tool-Ausfuehrung
- `structlog` fuer strukturierte JSON-Logs
- `prometheus_client` fuer Metriken
- OpenTelemetry fuer Tracing
- `sentry-sdk` fuer Error-Tracking
- `pytest`, `ruff` und `mypy` fuer Qualitaetssicherung
- Docker-first Runtime mit `Dockerfile` und `compose.yaml`
- ein lauffaehiger Worker mit sauberem Startup- und Shutdown-Verhalten
- CLI-Healthcheck mit strukturiertem JSON-Output
- sauberer Flush von Traces und Error-Events beim Shutdown

## Schnellstart

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run boilerplate run
```

## Docker

```bash
copy .env.example .env
docker compose up --build
```

Der Container startet den Worker, exponiert den Metrics-Port und verwendet den CLI-Healthcheck fuer Compose.
Wenn Metrics deaktiviert sind, bleibt der CLI-Healthcheck absichtlich erfolgreich, arbeitet dann aber nur als einfacher Liveness-Check ohne Scrape-Pruefung.
Wenn der Metrics-Endpunkt erreichbar ist, aber ungueltige Daten liefert, meldet der Healthcheck das explizit als Fehlerzustand statt unstrukturiert zu crashen.

## Wichtige Befehle

```bash
uv run boilerplate run
uv run boilerplate health
```

## Konfiguration

Die Basis-Konfiguration dieses Boilerplates kommt ausschliesslich aus Umgebungsvariablen. Das ist absichtlich so, damit ein Projekt vollstaendig ueber Docker und `docker-compose.yml` reproduzierbar bleibt.

YAML ist in diesem Boilerplate keine konkurrierende zweite Config-Quelle fuer dieselben Werte. Wenn ein Projekt spaeter eine YAML-Datei nutzt, dann nur fuer grosse, strukturierte Fachkonfiguration, die in ENV-Variablen unhandlich waere. Typischerweise wird so eine Datei selbst wieder ueber eine ENV wie `FEATURE_CONFIG_PATH` referenziert.

Wichtig:

- Runtime- und Betriebssettings leben in ENVs.
- Komplexe Fachkonfiguration darf in YAML leben.
- Dieselbe Einstellung sollte nicht parallel in ENV und YAML gepflegt werden.
- Es gibt bewusst keine Prioritaets- oder Override-Logik zwischen beiden.

## Relevante Runtime-Umgebungsvariablen

- `APP_NAME` Standard: `python-boilerplate`
- `APP_ENV` Standard: `development`
- `APP_VERSION` Standard: `0.1.0`
- `APP_COMMIT` Standard: `dev`
- `APP_INSTANCE` Standard: `local`
- `APP_LOG_LEVEL` Standard: `INFO`
- `APP_LOOP_INTERVAL_SECONDS` Standard: `5.0`
- `APP_METRICS_ENABLED` Standard: `true`
- `APP_METRICS_HOST` Standard: `0.0.0.0`
- `APP_METRICS_PORT` Standard: `9000`
- `APP_HEALTH_MAX_AGE_SECONDS` Standard: `60.0`
- `APP_TRACES_ENABLED` Standard: `true`
- `APP_TRACES_SAMPLE_RATE` Standard: `1.0`
- `OTEL_EXPORTER_OTLP_ENDPOINT` Optional fuer OTLP/HTTP Export
- `SENTRY_DSN` Optional fuer Sentry

## YAML in Projekten

Wenn ein konkretes Projekt zusaetzlich YAML braucht, sollte es das so handhaben:

- eine ENV enthaelt den Pfad zur YAML-Datei
- die YAML beschreibt nur komplexe Fachlogik oder grosse strukturierte Daten
- die Runtime-Settings aus `config/settings.py` bleiben davon unberuehrt

Das Boilerplate bringt dafuer absichtlich keine Beispiel-YAML mit, weil deren Struktur projektspezifisch sein sollte.

## Projektstruktur

```text
.
.github/workflows/ci.yml
docs/observability.md
pyproject.toml
Dockerfile
compose.yaml
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
    ├── bootstrap.py
    ├── errors.py
    ├── logging.py
    ├── metrics.py
    └── tracing.py
tests/
├── test_cli.py
├── test_config.py
└── test_health.py
```

## Observability

Die Baseline ist absichtlich verpflichtend. Neue Features sollen die vorhandenen Helfer unter `src/python_boilerplate/observability/` nutzen, nicht ihre eigene Logging-, Metrics-, Tracing- oder Sentry-Konfiguration mitbringen.
Der eingebaute Healthcheck bewertet standardmaessig `app_up` und nutzt fuer Frische bevorzugt `last_success_timestamp_seconds`. Wenn dieses Signal in einem konkreten Dienst nicht existiert, faellt er auf `last_progress_timestamp_seconds` zurueck. Dabei zaehlt auch fehlgeschlagene Arbeit weiterhin als Progress-Signal; nur die Erfolgsfrische bleibt bewusst strenger.

Die volle Konvention steht in [docs/observability.md](docs/observability.md).
Das Konfigurationsmodell steht in [docs/configuration.md](docs/configuration.md).

## Strukturgedanke

- `app.py` ist der Composition Root fuer den Zusammenbau der Anwendung.
- `config/` kapselt ENV-basierte Runtime-Settings.
- `runtime/` enthaelt betriebliche Themen wie Health und Lifecycle-nahe Helfer.
- `services/` ist der Ort fuer konkrete Laufzeitmodelle wie Worker oder Scheduler. Ein HTTP-Service-Skelett gehoert aktuell nicht zum Boilerplate.
- Iterationen in `services/` sollen kooperativ auf ein `stop_event` reagieren, damit Deployments und Container-Shutdowns nicht an lang laufenden Arbeitsschritten haengen bleiben.
- `observability/` bleibt der zentrale Einstieg fuer Logging, Metrics, Tracing und Error-Tracking.
