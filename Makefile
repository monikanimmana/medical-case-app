.PHONY: help install db-up db-down reproduce clean

help:
	@echo "AI Support Agent — Available commands:"
	@echo "  make install      Install dependencies"
	@echo "  make db-up        Start Postgres + pgvector"
	@echo "  make db-down      Stop database"
	@echo "  make reproduce    Run full pipeline (15 min, small subsample)"
	@echo "  make clean        Remove artifacts"

install:
	pip install -r requirements.txt

db-up:
	docker-compose up -d
	@echo "Database is running. Use 'docker-compose logs -f' to monitor."

db-down:
	docker-compose down

reproduce:
	python -m src.pipeline --brand [BRAND] --sample-size 5000

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov

.DEFAULT_GOAL := help
