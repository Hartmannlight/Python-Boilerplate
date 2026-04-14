# Configuration Model

This boilerplate is intentionally `ENV-first`.

## Principle

All runtime and operational settings come from environment variables.
That includes settings such as:

- service identity
- environment name
- log level
- metrics enablement and port
- trace exporter endpoint
- Sentry DSN

The reason is operational simplicity: projects based on this boilerplate are expected to run in Docker and be recoverable from their container configuration alone.

The current boilerplate scope is intentionally narrow:

- worker-style services
- schedulers and cron-like processes
- small non-HTTP background services

If a concrete project needs an HTTP API or a different runtime model, add that structure deliberately instead of assuming it already exists in the template.

## YAML usage

Optional YAML files are allowed, but they are not a second general-purpose settings layer.

YAML is intended only for configuration that is:

- large
- structured
- nested
- difficult to maintain as flat environment variables

Examples:

- mapping tables
- routing rules
- provider-specific transformation rules
- content or workflow definitions

## Non-goal

This boilerplate does not support:

- ENV-overrides-YAML precedence for the same setting
- YAML-overrides-ENV precedence for the same setting
- mixed ownership where one config value may live in either place

If a setting is operational, it belongs in ENV.
If it is large and domain-specific, it may live in YAML.

## Recommended pattern

Use an ENV to point to a project-specific YAML file:

```env
FEATURE_CONFIG_PATH=/app/config/feature-config.yml
```

Then load that YAML only inside the relevant project feature or adapter layer.
Do not merge it into the boilerplate runtime `Settings` model.

## Current boilerplate runtime settings

The runtime settings model lives in `src/python_boilerplate/config/settings.py`.
It is intentionally limited to ENV-based operational settings.
