<p align="center">
  <a href="https://quack-ai.com"><img src="https://uploads-ssl.webflow.com/64a6527708bc7f2ce5fd6b2a/64a654825ed3d444b47c4935_quack-logo%20(copy).png" width="75" height="75"></a>
</p>
<h1 align="center">
 API for contribution assistance
</h1>

<p align="center">
  <a href="https://github.com/quack-ai/contribution-api/actions?query=workflow%3Abuilds">
    <img alt="CI Status" src="https://img.shields.io/github/actions/workflow/status/quack-ai/contribution-api/builds.yml?branch=main&label=CI&logo=github&style=flat-square">
  </a>
  <a href="http://quack-ai.github.io/contribution-api">
    <img src="https://img.shields.io/github/actions/workflow/status/quack-ai/contribution-api/builds.yml?branch=main&label=docs&logo=read-the-docs&style=flat-square" alt="Documentation Status">
  </a>
  <a href="https://codecov.io/gh/quack-ai/contribution-api">
    <img src="https://img.shields.io/codecov/c/github/quack-ai/contribution-api.svg?logo=codecov&style=flat-square" alt="Test coverage percentage">
  </a>
  <a href="https://github.com/ambv/black">
    <img src="https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square" alt="black">
  </a>
  <a href="https://github.com/PyCQA/bandit">
    <img src="https://img.shields.io/badge/security-bandit-yellow.svg?style=flat-square" alt="bandit">
  </a>
  <a href="https://www.codacy.com/gh/quack-ai/contribution-api/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=quack-ai/contribution-api&amp;utm_campaign=Badge_Grade"><img src="https://app.codacy.com/project/badge/Grade/f8b24d4f9f674ef487b0889b2aa90e9c"/></a>
</p>
<p align="center">
  <img alt="GitHub release (latest by date)" src="https://img.shields.io/github/v/release/quack-ai/contribution-api">
  <img alt="GitHub" src="https://img.shields.io/github/license/quack-ai/contribution-api">
</p>


The building blocks of our contribution assistance API.

## Quick Tour

### Running/stopping the service

You can run the API containers using this command:

```shell
make run
```

You can now navigate to [`http://api.localhost:8050/docs`](http://api.localhost:8050/docs) to interact with the API (or do it through HTTP requests) and explore the documentation.

In order to stop the service, run:
```shell
make stop
```


### How is the database organized

The back-end core feature is to interact with the metadata tables. For the service to be useful for codebase analysis, multiple tables/object types are introduced and described as follows:

#### Access-related tables

- Users: stores the hashed credentials and access level for users & devices.

#### Core worklow tables

- Repository: metadata of installed repositories.
- Guideline: metadata of curated guidelines.

![UML diagram](https://private-user-images.githubusercontent.com/26927750/256741892-d7c54788-c36b-4bda-bd14-344cec30ec96.svg?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTEiLCJleHAiOjE2OTA1ODQ2NTAsIm5iZiI6MTY5MDU4NDM1MCwicGF0aCI6Ii8yNjkyNzc1MC8yNTY3NDE4OTItZDdjNTQ3ODgtYzM2Yi00YmRhLWJkMTQtMzQ0Y2VjMzBlYzk2LnN2Zz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFJV05KWUFYNENTVkVINTNBJTJGMjAyMzA3MjglMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjMwNzI4VDIyNDU1MFomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTA3MGVmYjMxODA0YzRjZTJjNWE4NmY4NmI4NmY4NTk0YTczOGQ4MzM2OGY5ZGZmMjkwMzUwZWU4NDg2OTcxYzcmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0JmFjdG9yX2lkPTAma2V5X2lkPTAmcmVwb19pZD0wIn0.YiGSrVAQ3TY3ziwoKqFfgorl5KzOEoONh_N7uRkjCX8)

## Installation

### Prerequisites

- [Docker](https://docs.docker.com/engine/install/)
- [Docker compose](https://docs.docker.com/compose/)
- [Make](https://www.gnu.org/software/make/) (optional)

The project was designed so that everything runs with Docker orchestration (standalone virtual environment), so you won't need to install any additional libraries.

## Configuration

In order to run the project, you will need to specific some information, which can be done using a `.env` file.
This file will have to hold the following information:
- `POSTGRES_DB`: the name of the [PostgreSQL](https://www.postgresql.org/) database that will be created
- `POSTGRES_USER`: the login to the PostgreSQL database
- `POSTGRES_PASSWORD`: the password to the PostgreSQL database
- `SUPERUSER_LOGIN`: the login of the initial admin access
- `SUPERUSER_ID`: the GitHub ID of the initial admin access
- `SUPERUSER_PWD`: the password of the initial admin access
- `GH_OAUTH_ID`: the ID of the GitHub Oauth app
- `GH_OAUTH_SECRET`: the secret of the GitHub Oauth app

Optionally, the following information can be added:
- `SENTRY_DSN`: the URL of the [Sentry](https://sentry.io/) project, which monitors back-end errors and report them back.
- `SERVER_NAME`: the server tag to apply to events.

So your `.env` file should look like something similar to:
```
POSTGRES_DB=review_db
POSTGRES_USER=admin
POSTGRES_PASSWORD=my_password
SUPERUSER_LOGIN=superadmin
SUPERUSER_PWD=super_password
SUPERUSER_ID=1
SENTRY_DSN='https://replace.with.you.sentry.dsn/'
SENTRY_SERVER_NAME=my_storage_bucket_name
GH_OAUTH_ID=your_github_oauth_app_id
GH_OAUTH_SECRET=your_github_oauth_app_secret
```

The file should be placed at the root folder of your local copy of the project.

## More goodies

### Documentation

The full package documentation is available [here](https://quack-ai.github.io/contribution-api) for detailed specifications.


## Contributing

Any sort of contribution is greatly appreciated!

You can find a short guide in [`CONTRIBUTING`](CONTRIBUTING.md) to help grow this project!


## Copying & distribution

Copyright (C) 2023, Quack AI.

All rights reserved.
Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.
