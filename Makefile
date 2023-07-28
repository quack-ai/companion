# this target runs checks on all files
quality:
	ruff check .
	mypy
	black --check .
	bandit -r . -c pyproject.toml

# this target runs checks on all files and potentially modifies some of them
style:
	black .
	ruff --fix .

# Pin the dependencies
lock:
	poetry lock

# Build the docker
build:
	poetry export -f requirements.txt --without-hashes --output requirements.txt
	git submodule update --init --recursive
	docker build . -t quackai/contribution-api:python3.9-alpine3.14

# Run the docker
run:
	poetry export -f requirements.txt --without-hashes --output requirements.txt
	git submodule update --init --recursive
	docker compose up -d --build

# Run the docker
stop:
	docker compose down

add-revision:
	docker compose exec backend alembic revision --autogenerate

apply-revision:
	docker compose exec backend alembic upgrade head


# Run tests for the library
e2e:
	poetry export -f requirements.txt --without-hashes --output requirements.txt
	docker compose -f docker-compose.test.yml up -d --build
	sleep 5
	python scripts/test_e2e.py
	docker compose -f docker-compose.test.yml down
