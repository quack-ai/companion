# Contributing to Quack 🦆

Welcome 🤗
The resources compiled here are meant to help developers contribute to the project. Please check the [code of conduct](CODE_OF_CONDUCT.md) before going further.

If you're looking for ways to contribute, here are some ideas:
- 🐛 Report bugs (open an [issue](https://github.com/quack-ai/contribution-api/issues/new?labels=type%3A+bug&template=bug_report.yml) & fill the template)
- 💡 Suggest improvements (open a [GitHub discussion](https://github.com/quack-ai/contribution-api/discussions/new?category=ideas) or chat with us on [Discord](https://discord.gg/E9rY3bVCWd))
- 👍👎 Provide feedback about our [roadmap](https://docs.quackai.com/community/roadmap) (easier to chat on [Discord](https://discord.gg/E9rY3bVCWd))
- ⌨️ Update the codebase (check our guide for [setup](#developer-setup) & [PR submission](#submitting-a-pull-request))


## Data model

The back-end core feature is to interact with the metadata tables. For the service to be useful for codebase analysis, multiple tables/object types are introduced and described as follows:

#### Access-related tables

- Users: stores the hashed credentials and access level for users & devices.

#### Core worklow tables

- Repository: metadata of installed repositories.
- Guideline: metadata of curated guidelines.

![UML diagram](https://github.com/quack-ai/contribution-api/assets/26927750/509dc855-547e-45c3-a545-a29e8ce3712c)


## Codebase structure

- [`src/app`](https://github.com/quack-ai/contribution-api/blob/main/src/app) - The actual API codebase
- [`src/tests`](https://github.com/quack-ai/contribution-api/blob/main/src/tests) - The API unit tests
- [`.github`](https://github.com/quack-ai/contribution-api/blob/main/.github) - Configuration for CI (GitHub Workflows)
- [`docker`](https://github.com/quack-ai/contribution-api/blob/main/docker) - Docker-related configurations
- [`docs`](https://github.com/quack-ai/contribution-api/blob/main/docs) - Everything related to documentation
- [`scripts`](https://github.com/quack-ai/contribution-api/blob/main/scripts) - Custom scripts
- [`demo`](https://github.com/quack-ai/contribution-api/blob/main/demo) - Code for the Gradio demo


## Continuous Integration

This project uses the following integrations to ensure proper codebase maintenance:

- [Github Worklow](https://help.github.com/en/actions/configuring-and-managing-workflows/configuring-a-workflow) - run jobs for package build and coverage
- [Codacy](https://www.codacy.com/) - analyzes commits for code quality
- [Codecov](https://codecov.io/) - reports back coverage results
- [Sentry](https://docs.sentry.io/platforms/python/) - automatically reports errors back to us
- [PostgreSQL](https://www.postgresql.org/) - storing and interacting with the metadata database
- [PostHog](https://posthog.com/) - product analytics
- [Slack](https://slack.com/) - event notifications
- [Prometheus](https://prometheus.io/) - Scraping API metrics
- [Grafana](https://grafana.com/) - Dashboard for API monitoring (dashboard adapted from https://github.com/Kludex/fastapi-prometheus-grafana)
- [Traefik](https://traefik.io/) - the reverse proxy and load balancer

As a contributor, you will only have to ensure coverage of your code by adding appropriate unit testing of your code.



## Feedback

### Feature requests & bug report

Whether you encountered a problem, or you have a feature suggestion, your input has value and can be used by contributors to reference it in their developments. For this purpose, we advise you to use Github [issues](https://github.com/quack-ai/contribution-api/issues).

First, check whether the topic wasn't already covered in an open / closed issue. If not, feel free to open a new one! When doing so, use issue templates whenever possible and provide enough information for other contributors to jump in.

### Questions

If you are wondering how to do something with Contribution API, or a more general question, you should consider checking out Github [discussions](https://github.com/quack-ai/contribution-api/discussions). See it as a Q&A forum, or the project-specific StackOverflow!


## Developer setup

### Prerequisites

- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [Docker](https://docs.docker.com/engine/install/)
- [Docker compose](https://docs.docker.com/compose/)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) and a GPU (>= 6 Gb VRAM for good performance/latency balance)
- [Poetry](https://python-poetry.org/docs/)
- [Make](https://www.gnu.org/software/make/) (optional)


### Configure your fork

1 - Fork this [repository](https://github.com/quack-ai/contribution-api) by clicking on the "Fork" button at the top right of the page. This will create a copy of the project under your GitHub account (cf. [Fork a repo](https://docs.github.com/en/get-started/quickstart/fork-a-repo)).

2 - [Clone your fork](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository) to your local disk and set the upstream to this repo
```shell
git clone git@github.com:<YOUR_GITHUB_ACCOUNT>/contribution-api.git
cd contribution-api
git remote add upstream https://github.com/quack-ai/contribution-api.git
```

### Install the dependencies

Let's install the different libraries:
```shell
poetry export -f requirements.txt --without-hashes --with quality --output requirements.txt
pip install -r requirements.txt
```

#### Pre-commit hooks
Let's make your life easier by formatting & fixing lint on each commit:
```shell
pre-commit install
```

### Environment configuration

In order to run the project, you will need to specific some information, which can be done using a `.env` file.
Copy the default environement variables from [`.env.example`](./.env.example):
```shell
cp .env.example .env
```

This file contains all the information to run the project.

#### Values you have to replace
- `SUPERADMIN_GH_PAT`: the [GitHub personal access token](https://github.com/settings/tokens?type=beta) of the initial admin user
- `GH_OAUTH_ID`: the Client ID of the GitHub Oauth app (Create an OAuth app on [GitHub](https://github.com/settings/applications/new), pointing to your Quack dashboard w/ callback URL)
- `GH_OAUTH_SECRET`: the secret of the GitHub Oauth app (Generate a new client secret on the created OAuth app)

#### Values you can edit freely
- `POSTGRES_DB`: a name for the [PostgreSQL](https://www.postgresql.org/) database that will be created
- `POSTGRES_USER`: a login for the PostgreSQL database
- `POSTGRES_PASSWORD`: a password for the PostgreSQL database
- `SUPERADMIN_LOGIN`: the login of the initial admin user
- `SUPERADMIN_PWD`: the password of the initial admin user

#### Other optional values
- `SECRET_KEY`: if set, tokens can be reused between sessions. All instances sharing the same secret key can use the same token.
- `OLLAMA_MODEL`: the model tag in [Ollama library](https://ollama.com/library) that will be used for the API.
- `SENTRY_DSN`: the DSN for your [Sentry](https://sentry.io/) project, which monitors back-end errors and report them back.
- `SERVER_NAME`: the server tag that will be used to report events to Sentry.
- `POSTHOG_KEY`: the project API key for PostHog [PostHog](https://eu.posthog.com/settings/project-details).
- `SLACK_API_TOKEN`: the App key for your Slack bot (Create New App on [Slack](https://api.slack.com/apps), go to OAuth & Permissions and generate a bot User OAuth Token).
- `SLACK_CHANNEL`: the Slack channel where your bot will post events (defaults to `#general`, you have to invite the App to your channel).
- `SUPPORT_EMAIL`: the email used for support of your API.
- `DEBUG`: if set to false, silence debug logs.

## Submitting a Pull Request

### Preparing your local branch

You should not work on the `main` branch, so let's create a new one
```shell
git checkout -b a-short-description
```

### Developing your feature

#### Commits

- **Code**: ensure to provide docstrings to your Python code. In doing so, please follow [Google-style](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) so it can ease the process of documentation later.
- **Commit message**: please follow [Angular commit format](https://github.com/angular/angular/blob/main/CONTRIBUTING.md#-commit-message-format)

#### Tests

In order to run the same tests as the CI workflows, you can run them locally:

```shell
make test
```

#### Code quality

To run all quality checks together

```shell
make quality
```

The previous command won't modify anything in your codebase. Some fixes (import ordering and code formatting) can be done automatically using the following command:

```shell
make style
```

### Submit your modifications

Push your last modifications to your remote branch
```shell
git push -u origin a-short-description
```

Then [open a Pull Request](https://docs.github.com/en/github/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request) from your fork's branch. Follow the instructions of the Pull Request template and then click on "Create a pull request".
