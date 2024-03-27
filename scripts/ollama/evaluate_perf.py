# Copyright (C) 2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict

import numpy as np
import requests
from tqdm import tqdm

logger = logging.getLogger(__name__)


def _stream_response(
    endpoint: str,
    model: str,
    system: str,
    prompt: str,
    temperature: float = 0.0,
    timeout: int = 60,
    keep_alive: str = "1s",
) -> Dict[str, Any]:
    session = requests.Session()
    stream_ts = [time.perf_counter()]
    with session.post(
        f"{endpoint}/api/chat",
        json={
            "model": model,
            "stream": True,
            "options": {"temperature": temperature},
            "keep_alive": keep_alive,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        },
        timeout=timeout,
        stream=True,
    ) as response:
        for _chunk in response.iter_lines():
            stream_ts.append(time.perf_counter())  # noqa PERF401
        data = json.loads(_chunk.decode())
    ollama_stat_keys = {
        "total_duration",
        "load_duration",
        "prompt_eval_duration",
        "prompt_eval_count",
        "eval_count",
        "eval_duration",
    }
    return {
        # Actual measurement (in seconds)
        "ttft": stream_ts[1] - stream_ts[0],
        "generation_latency": [after - before for before, after in zip(stream_ts[1:-1], stream_ts[2:])],
        # Ollama (in nanoseconds)
        "ollama": {k: v for k, v in data.items() if k in ollama_stat_keys},
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
    _stream_response(args.endpoint, args.model, SYSTEM_PROMPT, "Hello")
    # Evaluation run
    ttft, out_latency, load_duration, in_tokens, in_duration, out_tokens, out_duration = [], [], [], [], [], [], []
    for user_prompt in tqdm(USER_PROMPTS * args.it):
        result = _stream_response(args.endpoint, args.model, SYSTEM_PROMPT, user_prompt, args.temperature)
        ttft.append(result["ttft"])
        out_latency.extend(result["generation_latency"])
        in_tokens.append(result["ollama"]["prompt_eval_count"])
        out_tokens.append(result["ollama"]["eval_count"])
        in_duration.append(result["ollama"]["prompt_eval_duration"])
        out_duration.append(result["ollama"]["eval_duration"])
        load_duration.append(result["ollama"]["load_duration"])
    # Aggregate information
    in_duration = np.array(in_duration, dtype=int)
    out_duration = np.array(out_duration, dtype=int)
    load_duration = np.array(load_duration, dtype=int)
    # Tokens (np.float64 to handle NaNs)
    in_tokens = np.array(in_tokens, dtype=np.float64)
    out_tokens = np.array(out_tokens, dtype=np.float64)
    ttft = np.array(ttft, dtype=np.float64)
    out_latency = np.array(out_latency, dtype=np.float64)

    print(f"{args.model} ({args.it} runs) at {datetime.now(timezone.utc)}")
    # HTTP timing
    print(
        f"HTTP: ttft {1000 * ttft.mean():.2f}ms (± {1000 * ttft.std():.2f})"
        f" | ingestion {in_tokens.sum() / ttft.sum():.2f} tok/s (± {(in_tokens / ttft).std():.2f})"
        f" | generation {(1 / out_latency).mean():.2f} tok/s (± {(1 / out_latency).std():.2f})"
    )
    # Ollama-reported stats
    print(
        f"Ollama-reported: load duration {load_duration.mean() / 1e6:.2f}ms (± {load_duration.std() / 1e6:.2f})"
        f" | ingestion {1e9 * in_tokens.sum() / in_duration.sum():.2f} tok/s (± {1e9 * (in_tokens / in_duration).std():.2f})"
        f" | generation {1e9 * out_tokens.sum() / out_duration.sum():.2f} tok/s (± {1e9 * (out_tokens / out_duration).std():.2f})"
    )


def get_parser():
    import argparse

    parser = argparse.ArgumentParser(
        description="Ollama speed evaluation", formatter_class=argparse.ArgumentDefaultsHelpFormatter
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
