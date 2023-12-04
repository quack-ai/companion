# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

import logging
from typing import Dict, List, Tuple, Union

import requests
from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

__all__ = ["slack_client"]


class SlackClient:
    ENDPOINT: str = "https://slack.com/api"

    def __init__(self, default_channel: str, api_token: Union[str, None] = None) -> None:
        self.is_enabled = False
        if isinstance(api_token, str):
            self.headers = self._get_headers(api_token)
            # Validate token
            response = requests.post(f"{self.ENDPOINT}/auth.test", headers=self.headers, timeout=2)
            json_response = response.json()
            if response.status_code != 200 or not json_response["ok"]:
                raise HTTPException(status_code=response.status_code, detail=json_response.get("error"))
            self.default_channel = default_channel
            self.is_enabled = True
            logger.info(
                f"Using Slack bot {json_response['user']} (space: {json_response['url']} | channel: {default_channel})"
            )

    @staticmethod
    def _get_headers(api_key: str) -> Dict[str, str]:
        return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def post_message(self, channel: str, text: str) -> Dict[str, str]:
        response = requests.post(
            f"{self.ENDPOINT}/chat.postMessage",
            headers=self.headers,
            timeout=2,
            json={"channel": channel, "text": text},
        )
        json_response = response.json()
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=json_response.get("error"))

        return json_response

    def notify(self, title: str, quoted_elements: List[Tuple[str, str]]) -> Dict[str, str]:
        if not self.is_enabled:
            return {}
        block_quote = "\n".join(f"> {key}: {val}" for key, val in quoted_elements)
        return self.post_message(self.default_channel, f"{title}\n{block_quote}")


slack_client = SlackClient(settings.SLACK_CHANNEL, settings.SLACK_API_TOKEN)
