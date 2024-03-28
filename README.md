<p align="center">
  <a href="https://quackai.com"><img src="https://uploads-ssl.webflow.com/64a6527708bc7f2ce5fd6b2a/64a654825ed3d444b47c4935_quack-logo%20(copy).png" width="75" height="75"></a>
</p>
<h1 align="center">
 Quack Companion - Type smarter, ship faster
</h1>
<p align="center">
  <a href="https://github.com/quack-ai/companion">API</a> ・
  <a href="https://github.com/quack-ai/companion-vscode">VSCode extension</a> ・
  <a href="https://docs.quackai.com">Documentation</a>
</p>
<h2 align="center"></h2>

<p align="center">
  <a href="https://github.com/quack-ai/companion/actions?query=workflow%3Abuilds">
    <img alt="CI Status" src="https://img.shields.io/github/actions/workflow/status/quack-ai/companion/builds.yml?branch=main&label=CI&logo=github&style=flat-square">
  </a>
  <a href="https://github.com/astral-sh/ruff">
    <img src="https://img.shields.io/badge/Linter-Ruff-FCC21B?style=flat-square&logo=ruff&logoColor=white" alt="ruff">
  </a>
  <a href="https://www.codacy.com/gh/quack-ai/companion/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=quack-ai/companion&amp;utm_campaign=Badge_Grade"><img src="https://app.codacy.com/project/badge/Grade/b51832763a394255941b541b0813750c"/></a>
  <a href="https://codecov.io/gh/quack-ai/companion">
    <img src="https://img.shields.io/codecov/c/github/quack-ai/companion.svg?logo=codecov&style=flat-square&token=fkT0jQefhO" alt="Test coverage percentage">
  </a>
</p>
<p align="center">
  <a href="https://marketplace.visualstudio.com/items?itemName=quackai.quack-companion">
    <img src="https://img.shields.io/visual-studio-marketplace/v/quackai.quack-companion?logo=visualstudiocode&logoColor=fff&style=flat-square&label=VS%20Marketplace" alt="VS Marketplace">
  </a>
  <a href="https://open-vsx.org/extension/quackai/quack-companion">
    <img src="https://img.shields.io/open-vsx/v/quackai/quack-companion?logo=opensourceinitiative&logoColor=fff&style=flat-square&label=Open%20VSX" alt="Open VSX Registry">
  </a>
  <img alt="GitHub release (latest by date)" src="https://img.shields.io/github/v/release/quack-ai/companion?label=Release&logo=github">
  <a href="https://hub.docker.com/repository/docker/quackai/companion">
    <img src="https://img.shields.io/docker/v/quackai/companion?style=flat-square&logo=Docker&logoColor=fff&label=Docker" alt="Docker image">
  </a>
  <a href="https://github.com/quack-ai/companion/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/quack-ai/companion.svg?label=License&logoColor=fff&style=flat-square" alt="License">
  </a>
</p>
<p align="center">
  <a href="https://discord.gg/E9rY3bVCWd">
    <img src="https://img.shields.io/badge/Discord-Community-5865F2?style=flat-square&logo=discord&logoColor=white" />
  </a>
  <a href="https://twitter.com/quack_ai">
    <img src="https://img.shields.io/badge/-@quack_ai-1D9BF0?style=flat-square&logo=twitter&logoColor=white" alt="Twitter">
  </a>
</p>

Quack companion helps software teams ship faster. See it as an instantly onboarded team member with full knowledge of your internal libraries and coding standards 🦆


## Quick Tour

### Code chat endpoint

![Code chat demo](https://github.com/quack-ai/companion/assets/26927750/dd705cfb-a964-4ca6-ad2e-8d15e7c314a7)

The backend API is the gatekeeper for your LLM inference container (powered by our friend at [Ollama](https://github.com/ollama/ollama)). With your services up and running, you can use the code chat endpoint as coding-specific LLM chat.

*Check our [LLM latency benchmark](scripts/ollama) on a few cloud providers if you want to run this in the cloud.*

### REST API for guideline management & LLM inference

With the service running, you can navigate to [`http://localhost:5050/docs`](http://localhost:5050/docs) to interact with the API (or do it through HTTP requests) and explore the documentation.

![API Swagger screenshot](https://github.com/quack-ai/companion/assets/26927750/b2701225-ce12-4e6a-bb43-6752683bd335)


## Get started 🚀

### Prerequisites

- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [Docker](https://docs.docker.com/engine/install/)
- [Docker compose](https://docs.docker.com/compose/)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) and a GPU (>= 6 Gb VRAM for good performance/latency balance)

### 60 seconds setup ⏱️

#### 1 - Clone the repository
```shell
git clone https://github.com/quack-ai/companion.git && cd companion
```
#### 2 - Set your environment variables
First copy the examples
```shell
cp .env.example .env
```
and then edit it:
```shell
nano .env
```
Replace the value of SUPERADMIN_GH_PAT with your GitHub user Personal Access Token. You can create one [here](https://github.com/settings/tokens?type=beta) (no need for extra permissions i.e. read-only).

#### 3 - Start the services

```shell
docker compose pull
docker compose up
```

#### 4 - Check how what you've deployed

You can now access:
- your backend API at [http://localhost:5050/docs](http://localhost:5050/docs)
- your APM dashboard at [http://localhost:3000](http://localhost:3000/d/_quackapi_dashboard/quack-api-dashboard)
- your Gradio chat interface at [http://localhost:7860](http://localhost:7860)


## Contributing

Oh hello there 👋 If you've scrolled this far, we bet it's because you like open-source. Do you feel like integrating a new LLM backend? Or perhaps improve our documentation? Or contributing in any other way?

You're in luck! You'll find everything you need in our [contributing guide](CONTRIBUTING.md) to help grow this project! And if you're interested, you can join us on [Discord](https://discord.gg/E9rY3bVCWd) 🤗


## Copying & distribution

Copyright (C) 2023-2024, Quack AI.

This program is licensed under the Apache License 2.0.
See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fquack-ai%2Fcontribution-api.svg?type=large&issueType=license)](https://app.fossa.com/projects/git%2Bgithub.com%2Fquack-ai%2Fcompanion?ref=badge_large&issueType=license)
