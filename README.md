<p align="center">
  <a href="https://quackai.com"><img src="https://uploads-ssl.webflow.com/64a6527708bc7f2ce5fd6b2a/64a654825ed3d444b47c4935_quack-logo%20(copy).png" width="75" height="75"></a>
</p>
<h1 align="center">
 Quack - Type smarter, ship faster
</h1>
<p align="center">
  <a href="https://github.com/quack-ai/companion">VSCode extension</a> ・
  <a href="https://github.com/quack-ai/contribution-api">Backend API</a> ・
  <a href="https://docs.quackai.com">Documentation</a>
</p>
<h2 align="center"></h2>

<p align="center">
  <a href="https://github.com/quack-ai/contribution-api/actions?query=workflow%3Abuilds">
    <img alt="CI Status" src="https://img.shields.io/github/actions/workflow/status/quack-ai/contribution-api/builds.yml?branch=main&label=CI&logo=github&style=flat-square">
  </a>
  <a href="https://github.com/astral-sh/ruff">
    <img src="https://img.shields.io/badge/Linter-Ruff-FCC21B?style=flat-square&logo=ruff&logoColor=white" alt="ruff">
  </a>
  <a href="https://www.codacy.com/gh/quack-ai/contribution-api/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=quack-ai/contribution-api&amp;utm_campaign=Badge_Grade"><img src="https://app.codacy.com/project/badge/Grade/b51832763a394255941b541b0813750c"/></a>
  <a href="https://codecov.io/gh/quack-ai/contribution-api">
    <img src="https://img.shields.io/codecov/c/github/quack-ai/contribution-api.svg?logo=codecov&style=flat-square&token=fkT0jQefhO" alt="Test coverage percentage">
  </a>
</p>
<p align="center">
  <img alt="GitHub release (latest by date)" src="https://img.shields.io/github/v/release/quack-ai/contribution-api">
  <a href="https://hub.docker.com/repository/docker/quackai/contribution-api">
    <img src="https://img.shields.io/docker/v/quackai/contribution-api?style=flat-square&logo=Docker&logoColor=fff&label=Docker" alt="Docker image">
  </a>
  <a href="https://github.com/quack-ai/contribution-api/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/quack-ai/contribution-api.svg?label=License&logoColor=fff&style=flat-square" alt="License">
  </a>
</p>
<p align="center">
  <a target="_blank" href="https://discord.gg/E9rY3bVCWd" style="background:none">
    <img src="https://img.shields.io/badge/Discord-join-continue.svg?labelColor=191937&color=6F6FF7&logo=discord" />
  </a>
  <a href="https://twitter.com/quack_ai">
    <img src="https://img.shields.io/badge/-@quack_ai-1D9BF0?style=flat-square&logo=twitter&logoColor=white" alt="Twitter">
  </a>
</p>

Quack is the AI coding companion that helps software teams ship faster. See it as an instantly onboarded team member with full knowledge of your internal libraries and coding standards 🦆


## Quick Tour

### Code chat endpoint

![Code chat demo](https://github.com/quack-ai/contribution-api/assets/26927750/dd705cfb-a964-4ca6-ad2e-8d15e7c314a7)

The backend API is the gatekeeper for your LLM inference container (powered by our friend at [Ollama](https://github.com/ollama/ollama)). With your services up and running, you can use the code chat endpoint as coding-specific LLM chat.

### REST API for guideline management & LLM inference

With the service running, you can navigate to [`http://localhost:8050/docs`](http://localhost:8050/docs) to interact with the API (or do it through HTTP requests) and explore the documentation.

![API Swagger screenshot](https://github.com/quack-ai/contribution-api/assets/26927750/725e8308-ace1-40ed-b742-242f8186fec0)

### Latency benchmark

You crave for perfect codde suggestions, but you don't know whether it fits your needs in terms of latency?
In the table below, you will find a latency benchmark for all tested LLMs from Ollama:

| Model                                                        | Ingestion mean (std)   | Generation mean (std) |
| ------------------------------------------------------------ | ---------------------- | --------------------- |
| [tinyllama:1.1b-chat-v1-q4_0](https://ollama.com/library/tinyllama:1.1b-chat-v1-q4_0) | 2014.63 tok/s (±12.62) | 227.13 tok/s (±2.26)  |
| [dolphin-phi:2.7b-v2.6-q4_0](https://ollama.com/library/dolphin-phi:2.7b-v2.6-q4_0) | 684.07 tok/s (±3.85)   | 122.25 toks/s (±0.87) |
| [dolphin-mistral:7b-v2.6](https://ollama.com/library/dolphin-mistral:7b-v2.6) | 291.94 tok/s (±0.4)    | 60.56 tok/s (±0.15)   |


This benchmark was performed over 20 iterations on the same input sequence, on a **laptop** to better reflect performances that can be expected by common users. The hardware setup includes an [Intel(R) Core(TM) i7-12700H](https://ark.intel.com/content/www/us/en/ark/products/132228/intel-core-i7-12700h-processor-24m-cache-up-to-4-70-ghz.html) for the CPU, and a [NVIDIA GeForce RTX 3060](https://www.nvidia.com/fr-fr/geforce/graphics-cards/30-series/rtx-3060-3060ti/) for the laptop GPU.

You can run this latency benchmark for any Ollama model on your hardware as follows:
```bash
python scripts/evaluate_ollama_latency.py dolphin-mistral:7b-v2.6-dpo-laser-q4_0 --endpoint http://localhost:3000
```

*All script arguments can be checked using `python scripts/evaluate_ollama_latency.py --help`*


## Get started 🚀

### Prerequisites

- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [Docker](https://docs.docker.com/engine/install/)
- [Docker compose](https://docs.docker.com/compose/)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) and a GPU (>= 6 Gb VRAM for good performance/latency balance)

### 60 seconds setup

#### Clone the repository
```shell
git clone https://github.com/quack-ai/contribution-api.git && cd contribution-api
```
#### Set your environment variables
First copy the examples
```shell
cp .env.example .env
```
and then, in it, replace the value of SUPERADMIN_GH_PAT with your GitHub user Personal Access Token. You can create one [here](https://github.com/settings/tokens?type=beta) (no need for extra permissions i.e. read-only).

#### Start the services

```shell
docker compose pull
docker compose up
```

#### Check how what your API

You can now access your backend API at [http://localhost:5050/docs](http://localhost:5050/docs)

Additionally, you can run the Gradio demo

## Contributing

Any sort of contribution is greatly appreciated!

You can find a short guide in [`CONTRIBUTING`](CONTRIBUTING.md) to help grow this project! And if you're interested, you can join us on [![](https://img.shields.io/badge/Discord-join-continue.svg?labelColor=191937&color=6F6FF7&logo=discord)](https://discord.gg/E9rY3bVCWd)


## Copying & distribution

Copyright (C) 2023-2024, Quack AI.

This program is licensed under the Apache License 2.0.
See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fquack-ai%2Fcontribution-api.svg?type=large&issueType=license)](https://app.fossa.com/projects/git%2Bgithub.com%2Fquack-ai%2Fcontribution-api?ref=badge_large&issueType=license)
