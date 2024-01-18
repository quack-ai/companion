# Copyright (C) 2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import time
from typing import Any, Dict

import numpy as np
import requests
from tqdm import tqdm


def _generate(
    endpoint: str, model: str, system: str, prompt: str, temperature: float = 0.0, timeout: int = 60
) -> Dict[str, Any]:
    return requests.post(
        f"{endpoint}/api/generate",
        json={
            "model": model,
            "stream": False,
            "options": {"temperature": temperature},
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
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        },
        timeout=timeout,
    )


def _format_response(response, system, prompt) -> Dict[str, Any]:
    assert response.status_code == 200
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


def main(args):
    print(args)

    # Healthcheck on endpoint & model
    assert requests.get(f"{args.endpoint}/api/tags", timeout=2).status_code == 200
    response = requests.post(f"{args.endpoint}/api/pull", json={"name": args.model, "stream": False}, timeout=10)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Speed
    speed_system = (
        "You are a helpful assistant, you will be given a coding task. Answer correctly, otherwise someone will die."
    )
    speed_prompt = "Write a Python function to compute the n-th fibonacci number"
    # Warmup
    for _ in range(args.warmup):
        _generate(args.endpoint, args.model, speed_system, speed_prompt)
        # _format_response(response, speed_system, speed_prompt)

    # Run
    timings = []
    input_chars, output_chars = [], []
    input_tokens, output_tokens = [], []
    load_duration, input_duration, output_duration, total_duration = [], [], [], []
    for _ in tqdm(range(args.it)):
        start_ts = time.perf_counter()
        response = _generate(args.endpoint, args.model, speed_system, speed_prompt)
        timings.append(time.perf_counter() - start_ts)
        inference = _format_response(response, speed_system, speed_prompt)
        input_chars.append(inference["chars"]["input"])
        output_chars.append(inference["chars"]["output"])
        input_tokens.append(inference["tokens"]["input"])
        output_tokens.append(inference["tokens"]["output"])
        load_duration.append(inference["duration"]["model"])
        input_duration.append(inference["duration"]["input"])
        output_duration.append(inference["duration"]["output"])
        total_duration.append(inference["duration"]["total"])

    print(f"{args.model} ({args.it} runs)")
    timings = np.array(timings)
    load_duration = np.array(load_duration, dtype=int)
    input_duration = np.array(input_duration, dtype=int)
    output_duration = np.array(output_duration, dtype=int)
    total_duration = np.array(total_duration, dtype=int)
    print(f"Model load duration: mean {load_duration.mean() / 1e6:.2f}ms, std {load_duration.std() / 1e6:.2f}ms")
    # Tokens (np.float64 to handle NaNs)
    input_tokens = np.array(input_tokens, dtype=np.float64)
    output_tokens = np.array(output_tokens, dtype=np.float64)
    input_chars = np.array(input_chars, dtype=np.float64)
    output_chars = np.array(output_chars, dtype=np.float64)
    print(
        f"Input processing: mean {1e9 * input_tokens.sum() / input_duration.sum():.2f} tok/s, std {1e9 * (input_tokens / input_duration).std():.2f} tok/s"
    )
    print(
        f"Output generation: mean {1e9 * output_tokens.sum() / output_duration.sum():.2f} tok/s, std {1e9 * (output_tokens / output_duration).std():.2f} tok/s"
    )

    # Chars
    print(
        f"Input processing: mean {1e9 * input_chars.sum() / input_duration.sum():.2f} char/s, std {1e9 * (input_chars / input_duration).std():.2f} char/s"
    )
    print(
        f"Output generation: mean {1e9 * output_chars.sum() / output_duration.sum():.2f} char/s, std {1e9 * (output_chars / output_duration).std():.2f} char/s"
    )
    print(f"Overall latency (ollama): mean {total_duration.mean() / 1e6:.2f}ms, std {total_duration.std() / 1e6:.2f}ms")
    print(f"Overall latency (HTTP): mean {1000 * timings.mean():.2f}ms, std {1000 * timings.std():.2f}ms")


def get_parser():
    import argparse

    parser = argparse.ArgumentParser(
        description="Ollama latency evaluation", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Data & model
    group = parser.add_argument_group("Data & model")
    group.add_argument("model", type=str, help="model to use")
    group.add_argument("--endpoint", default="http://localhost:11434/api", type=str, help="Ollama endpoint")

    # Inference params
    group = parser.add_argument_group("Inference params")
    group.add_argument("--temperature", default=0, type=float, help="Temperature to use for model inference")

    # Inference params
    group = parser.add_argument_group("Evaluation")
    group.add_argument("--it", type=int, default=20, help="Number of iterations to run")
    group.add_argument("--warmup", type=int, default=5, help="Number of iterations for warmup")

    return parser


if __name__ == "__main__":
    args = get_parser().parse_args()
    main(args)
