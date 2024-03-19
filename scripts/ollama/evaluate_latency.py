# Copyright (C) 2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict

import numpy as np
import requests
from tqdm import tqdm

logger = logging.getLogger(__name__)


def _generate(
    endpoint: str, model: str, system: str, prompt: str, temperature: float = 0.0, timeout: int = 60
) -> Dict[str, Any]:
    return requests.post(
        f"{endpoint}/api/generate",
        json={
            "model": model,
            "stream": False,
            "options": {"temperature": temperature},
            "keep_alive": "1s",
            "system": system,
            "prompt": prompt,
        },
        timeout=timeout,
    )


def _chat_completion(
    endpoint: str, model: str, system: str, prompt: str, temperature: float = 0.0, timeout: int = 60
) -> Dict[str, Any]:
    return requests.post(
        f"{endpoint}/api/chat",
        json={
            "model": model,
            "stream": False,
            "options": {"temperature": temperature},
            "keep_alive": "1s",
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        },
        timeout=timeout,
    )


def _format_response(response, system, prompt) -> Dict[str, Any]:
    assert response.status_code == 200, print(response.__dict__)
    json_response = response.json()
    return {
        "duration": {
            "model": json_response.get("load_duration"),
            "input": json_response.get("prompt_eval_duration"),
            "output": json_response.get("eval_duration"),
            "total": json_response.get("total_duration"),
        },
        "tokens": {"input": json_response.get("prompt_eval_count"), "output": json_response.get("eval_count")},
        "chars": {
            "input": len(system) + len(prompt),
            "output": len(json_response.get("response") or json_response["message"]["content"]),
        },
    }


SYSTEM_PROMPT = (
    "You are a helpful assistant, you will be given a coding task. Answer correctly, otherwise someone will die."
)
USER_PROMPTS = (
    "Write a Python function to compute the n-th fibonacci number",
    "What's the difference between a Promise and an observable in Javascript",
    "How are you?",
    "Tell me about LLMs",
)


def main(args):
    print(args)

    # Healthcheck on endpoint & model
    assert requests.get(f"{args.endpoint}/api/tags", timeout=2).status_code == 200
    assert requests.post(f"{args.endpoint}/api/show", json={"name": args.model}, timeout=2).status_code == 200

    # Warmup
    _chat_completion(args.endpoint, args.model, SYSTEM_PROMPT, "Hello")
    # Evaluation run
    input_tokens, output_tokens, input_duration, output_duration, load_duration = [], [], [], [], []
    for user_prompt in tqdm(USER_PROMPTS * args.it):
        response = _chat_completion(args.endpoint, args.model, SYSTEM_PROMPT, user_prompt)
        inference = _format_response(response, SYSTEM_PROMPT, user_prompt)
        input_tokens.append(inference["tokens"]["input"])
        output_tokens.append(inference["tokens"]["output"])
        input_duration.append(inference["duration"]["input"])
        output_duration.append(inference["duration"]["output"])
        load_duration.append(inference["duration"]["model"])
    # Aggregate information
    input_duration = np.array(input_duration, dtype=int)
    output_duration = np.array(output_duration, dtype=int)
    load_duration = np.array(load_duration, dtype=int)
    # Tokens (np.float64 to handle NaNs)
    input_tokens = np.array(input_tokens, dtype=np.float64)
    output_tokens = np.array(output_tokens, dtype=np.float64)
    result = {
        "created_at": str(datetime.now(timezone.utc)),
        "ingestion_mean": 1e9 * input_tokens.sum() / input_duration.sum(),
        "ingestion_std": 1e9 * (input_tokens / input_duration).std(),
        "generation_mean": 1e9 * output_tokens.sum() / output_duration.sum(),
        "generation_std": 1e9 * (output_tokens / output_duration).std(),
        "load_mean": load_duration.mean() / 1e6,
        "load_std": load_duration.std() / 1e6,
    }

    print(f"{args.model} ({args.it} runs) at {result['created_at']}")
    print(f"Model load duration: mean {result['load_mean']:.2f}ms, std {result['load_std']:.2f}ms")
    print(f"Ingestion: mean {result['ingestion_mean']:.2f} tok/s, std {result['ingestion_std']:.2f} tok/s")
    print(f"Generation: mean {result['generation_mean']:.2f} tok/s, std {result['generation_std']:.2f} tok/s")


def get_parser():
    import argparse

    parser = argparse.ArgumentParser(
        description="Ollama latency evaluation", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Data & model
    group = parser.add_argument_group("LLM setup")
    group.add_argument("model", type=str, help="model to evaluate")
    group.add_argument(
        "--endpoint", default=os.getenv("OLLAMA_ENDPOINT", "http://ollama:11434"), type=str, help="Ollama endpoint"
    )

    # Inference params
    group = parser.add_argument_group("Inference params")
    group.add_argument("--temperature", default=0, type=float, help="Temperature to use for model inference")

    # # Inference params
    group = parser.add_argument_group("Evaluation")
    group.add_argument("--it", type=int, default=5, help="Number of iterations to run")
    # group.add_argument("--warmup", type=int, default=3, help="Number of iterations for warmup")

    return parser


if __name__ == "__main__":
    args = get_parser().parse_args()
    main(args)
