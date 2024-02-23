# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import logging
from typing import Union

from posthog import Posthog

from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

__all__ = ["telemetry_client"]


class TelemetryClient:
    def __init__(self, api_key: Union[str, None] = None) -> None:
        self.is_enabled = isinstance(api_key, str)
        if isinstance(api_key, str):
            self.ph_client = Posthog(project_api_key=api_key, host="https://eu.posthog.com")
            logger.info("PostHog enabled")

    def capture(self, *args, **kwargs) -> None:
        if self.is_enabled:
            self.ph_client.capture(*args, **kwargs)

    def identify(self, *args, **kwargs) -> None:
        if self.is_enabled:
            self.ph_client.identify(*args, **kwargs)

    def alias(self, *args, **kwargs) -> None:
        if self.is_enabled:
            self.ph_client.alias(*args, **kwargs)


telemetry_client = TelemetryClient(api_key=settings.POSTHOG_KEY)
