.PHONY: install dev demo test lint fmt cov clean preflight

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

preflight:
	python -m chakravyuh.demo --scenario colonial
	python -m chakravyuh.demo --scenario synnovis
	python -m chakravyuh.demo --hitl
	pytest
	ruff check src tests

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
