.PHONY: install dev demo test lint fmt cov clean

install:
	pip install -e .

dev:
	pip install -e ".[all]"

demo:
	python -m chakravyuh.demo

test:
	pytest

cov:
	pytest --cov=chakravyuh --cov-report=term-missing

lint:
	ruff check src tests

fmt:
	ruff check --fix src tests

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
