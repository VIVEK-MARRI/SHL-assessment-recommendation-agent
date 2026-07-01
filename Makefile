.PHONY: install lint test evaluation run docker-build docker-run docker-compose-up docker-compose-down

install:
	pip install --upgrade pip
	pip install -e .
	pip install pytest ruff

lint:
	ruff check .

test:
	pytest tests/ -q

evaluation:
	python scripts/run_evaluation.py --all

run:
	python scripts/run_server.py --reload

docker-build:
	docker build -t shl-agent:latest .

docker-run:
	docker run -p 8000:8000 --env-file .env shl-agent:latest

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down
