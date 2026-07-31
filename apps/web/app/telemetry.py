"""Optional Azure Monitor setup."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def configure_telemetry(connection_string: str | None) -> None:
    if not connection_string:
        return
    os.environ.setdefault("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "false")
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(connection_string=connection_string)
    except Exception as exc:
        logger.warning("Telemetry initialization failed: %s", type(exc).__name__)
