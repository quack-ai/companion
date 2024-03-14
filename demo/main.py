# Copyright (C) 2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List

import gradio as gr
import requests
from dotenv import load_dotenv


class SessionManager:
    def __init__(self) -> None:
        self._token = ""
        self._url = ""

    def set_token(self, token: str) -> None:
        self._token = token

    def set_url(self, url: str) -> None:
        self._url = url

    @property
    def auth(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    @property
    def login_endpoint(self) -> str:
        return f"{self._url}/login/creds"

    @property
    def chat_endpoint(self) -> str:
        return f"{self._url}/code/chat"


session_manager = SessionManager()


def get_token(endpoint: str, login: str, pwd: str) -> str:
    response = requests.post(
        endpoint,
        data={"username": login, "password": pwd},
        timeout=2,
    )
    if response.status_code != 200:
        raise ValueError(response.json()["detail"])
    return response.json()["access_token"]


def auth_gradio(username: str, password: str) -> bool:
    try:
        session_manager.set_token(get_token(session_manager.login_endpoint, username, password))
        return True
    except ValueError:
        return False
    return False


def chat_response(message: str, history: List[List[str]]) -> str:
    session = requests.Session()
    _history = [
        {"role": "user" if idx % 2 == 0 else "assistant", "content": msg}
        for hist in history
        for idx, msg in enumerate(hist)
    ]
    with session.post(
        session_manager.chat_endpoint,
        json={"messages": [*_history, {"role": "user", "content": message}]},
        headers=session_manager.auth,
        stream=True,
    ) as response:
        reply = ""
        for line in response.iter_lines():
            reply += json.loads(line.decode("utf-8"))["message"]["content"]
            yield reply


def main(args: argparse.Namespace) -> None:
    session_manager.set_url(args.api)
    # Run the interface
    interface = gr.ChatInterface(
        chat_response,
        chatbot=gr.Chatbot(
            elem_id="chatbot",
            label="Quack Companion",
            avatar_images=(
                "./demo/assets/profile-user.png",
                "https://www.quackai.com/_next/image?url=%2Fquack.png&w=64&q=75",
            ),
            likeable=True,
            bubble_full_width=False,
        ),
        textbox=gr.Textbox(placeholder="Ask me anything about programming", container=False, scale=7),
        title="Quack AI: type smarter, ship faster",
        retry_btn=None,
        undo_btn=None,
        css="./demo/styles/custom.css",
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
        submit_btn=gr.Button("", variant="primary", size="sm", icon="./demo/assets/paper-plane.png"),
        stop_btn=gr.Button("", variant="stop", size="sm", icon="./demo/assets/stop-button.png"),
    )
    if not args.auth:
        session_manager.set_token(
            get_token(session_manager.login_endpoint, os.environ["SUPERADMIN_LOGIN"], os.environ["SUPERADMIN_PWD"])
        )
    interface.launch(
        server_port=args.port,
        show_error=True,
        favicon_path=Path(__file__).resolve().parent.joinpath("favicon.ico"),
        auth=auth_gradio if args.auth else None,
        show_api=False,
    )


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Quack API demo",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--port", type=int, default=8001, help="Port on which the webserver will be run")
    parser.add_argument(
        "--api",
        type=str,
        default=os.getenv("API_URL", "http://localhost:8050/api/v1"),
        help="URL of your Quack API instance",
    )
    parser.add_argument("--auth", action="store_true", help="Use the creds from Auth UI instead of env variables")
    args = parser.parse_args()

    main(args)
