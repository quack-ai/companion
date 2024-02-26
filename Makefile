# this target runs checks on all files
quality:
	ruff format --check .
	ruff check .
	mypy

# this target runs checks on all files and potentially modifies some of them
style:
	ruff format .
	ruff --fix .

# Pin the dependencies
lock:
	poetry lock --no-update

# Build the docker
build:
	poetry export -f requirements.txt --without-hashes --output requirements.txt
	docker build . -t quackai/contribution-api:python3.9-alpine3.14

# Run the docker
run:
	poetry export -f requirements.txt --without-hashes --output requirements.txt
	docker compose up -d --build

# Run the docker
stop:
	docker compose down

run-dev:
	poetry export -f requirements.txt --without-hashes --with test --output requirements.txt
	docker compose -f docker-compose.test.yml up -d --build

stop-dev:
	docker compose -f docker-compose.test.yml down

# Run tests for the library
test:
	poetry export -f requirements.txt --without-hashes --with test --output requirements.txt
	docker compose -f docker-compose.test.yml up -d --build
	docker compose exec -T backend pytest --cov=app
	docker compose -f docker-compose.test.yml down

# Run tests for the library
e2e:
	poetry export -f requirements.txt --without-hashes --output requirements.txt
	docker compose -f docker-compose.test.yml up -d --build
	sleep 5
	python scripts/test_e2e.py
	docker compose -f docker-compose.test.yml down
