from __future__ import annotations

import signal
from dataclasses import dataclass, field
from threading import Event
from uuid import uuid4

from python_boilerplate.config import Settings
from python_boilerplate.observability import ObservabilityRuntime
from python_boilerplate.observability.errors import report_exception
from python_boilerplate.observability.metrics import start_iteration
from python_boilerplate.observability.tracing import root_span


@dataclass(slots=True)
class WorkerService:
    settings: Settings
    runtime: ObservabilityRuntime
    stop_event: Event = field(default_factory=Event)

    def install_signal_handlers(self) -> None:
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum: int, _frame: object) -> None:
        reason = "sigterm" if signum == signal.SIGTERM else "sigint"
        self.runtime.logger.info("shutting_down", reason=reason)
        self.stop_event.set()

    def run(self) -> int:
        self.install_signal_handlers()
        self.runtime.logger.info(
            "startup_success",
            config_source="environment",
            metrics_enabled=self.settings.metrics_enabled,
            traces_enabled=self.settings.traces_enabled,
            sentry_enabled=bool(self.settings.sentry_dsn),
        )
        exit_code = 0
        try:
            while not self.stop_event.is_set():
                self.run_iteration()
                self.stop_event.wait(self.settings.loop_interval_seconds)
        except Exception as exc:
            report_exception(exc)
            self.runtime.logger.exception(
                "crashed",
                error=str(exc),
                exception_type=type(exc).__name__,
            )
            exit_code = 1
        finally:
            self.runtime.metrics.mark_shutdown()
            self.runtime.shutdown()
        self.runtime.logger.info("shutdown_complete")
        return exit_code

    def run_iteration(self) -> None:
        timer = start_iteration(self.runtime.metrics)
        run_id = str(uuid4())
        iteration_logger = self.runtime.logger.bind(job_name="service_iteration", request_id=run_id)
        try:
            with root_span(
                self.runtime.tracer,
                "service.iteration",
                job_name="service_iteration",
                request_id=run_id,
            ):
                if self.stop_event.is_set():
                    iteration_logger.info("iteration_skipped", outcome="shutdown_requested")
                    return
                iteration_logger.info("iteration_started")
                self.execute_iteration(self.stop_event)
                timer.observe_success()
                iteration_logger.info("iteration_completed", outcome="success")
        except Exception as exc:
            timer.observe_failure()
            iteration_logger.warning(
                "iteration_failed",
                outcome="failure",
                error=str(exc),
                exception_type=type(exc).__name__,
            )
            raise

    def execute_iteration(self, stop_event: Event) -> None:
        stop_event.wait(timeout=0)
