# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

import logging
from typing import Union

from posthog import Posthog

from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

__all__ = ["analytics_client"]


class AnalyticsClient:
    def __init__(self, ph_api_key: Union[str, None] = None) -> None:
        self.is_enabled = isinstance(ph_api_key, str)
        if isinstance(ph_api_key, str):
            self.ph_client = Posthog(project_api_key=ph_api_key, host="https://eu.posthog.com")
            logger.info("PostHog enabled")

    def capture(self, *args, **kwargs) -> None:
        if self.is_enabled:
            self.ph_client.capture(*args, **kwargs)

    def identify(self, *args, **kwargs) -> None:
        if self.is_enabled:
            self.ph_client.identify(*args, **kwargs)


analytics_client = AnalyticsClient(ph_api_key=settings.POSTHOG_KEY)
