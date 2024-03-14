# Copyright (C) 2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import argparse
import json
import os
from functools import partial
from pathlib import Path
from typing import Dict, List

import gradio as gr
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "http://localhost:8050/api/v1"
LOGIN_ENDPOINT = f"{API_URL}/login/creds"
CHAT_ENDPOINT = f"{API_URL}/code/chat"
API_LOGIN: str = os.environ["SUPERADMIN_LOGIN"]
API_PWD: str = os.environ["SUPERADMIN_PWD"]


def get_token(endpoint: str, login: str, pwd: str, timeout: int = 5) -> str:
    response = requests.post(
        endpoint,
        data={"username": login, "password": pwd},
        timeout=timeout,
    )
    if response.status_code != 200:
        raise ValueError(response.json()["detail"])
    return response.json()["access_token"]


def chat_response(message: str, history: List[List[str]], headers: Dict[str, str]) -> str:
    session = requests.Session()
    _history = [
        {"role": "user" if idx % 2 == 0 else "assistant", "content": msg}
        for hist in history
        for idx, msg in enumerate(hist)
    ]
    with session.post(
        CHAT_ENDPOINT,
        json={"messages": [*_history, {"role": "user", "content": message}]},
        headers=headers,
        stream=True,
    ) as response:
        reply = ""
        for line in response.iter_lines():
            reply += json.loads(line.decode("utf-8"))["message"]["content"]
            yield reply


def main(args: argparse.Namespace) -> None:
    # Retrieve a token
    superuser_auth = {
        "Authorization": f"Bearer {get_token(LOGIN_ENDPOINT, API_LOGIN, API_PWD)}",
        "Content-Type": "application/json",
    }
    # Run the interface
    interface = gr.ChatInterface(
        partial(chat_response, headers=superuser_auth),
        chatbot=gr.Chatbot(
            elem_id="chatbot",
            label="Quack Companion",
            avatar_images=("./demo/profile-user.png", "https://www.quackai.com/_next/image?url=%2Fquack.png&w=64&q=75"),
            likeable=True,
            bubble_full_width=False,
        ),
        textbox=gr.Textbox(placeholder="Ask me anything about programming", container=False, scale=7),
        title="Quack AI: type smarter, ship faster",
        retry_btn=None,
        undo_btn=None,
        # css="#htext span {white-space: pre}footer {visibility: hidden}",
        css="./demo/custom.css",
        examples=["Write a Python function to compute the n-th Fibonacci number"],
        theme=gr.themes.Default(
            text_size="sm",
            font=[
                gr.themes.GoogleFont("Noto Sans"),
                gr.themes.GoogleFont("Roboto"),
                "ui-sans-serif",
                "system-ui",
                "sans-serif",
            ],
            primary_hue="purple",
            secondary_hue="purple",
        ),
        fill_height=True,
        submit_btn=gr.Button("", variant="primary", size="sm", icon="./demo/paper-plane.png"),
        stop_btn=gr.Button("", variant="stop", size="sm", icon="./demo/stop-button.png"),
    )

    interface.launch(
        server_port=args.port,
        show_error=True,
        favicon_path=Path(__file__).resolve().parent.joinpath("favicon.ico"),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Quack API demo",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--port", type=int, default=8001, help="Port on which the webserver will be run")
    args = parser.parse_args()

    main(args)
