.PHONY: test check install format clean all validate help

help:
	@echo "AEO Graph Engine - Developer Commands"
	@echo "====================================="
	@echo "make test       Run pytest test suite"
	@echo "make validate   Run built-in engine self-tests & validation"
	@echo "make install    Install package in editable mode"
	@echo "make clean      Remove build artifacts and caches"
	@echo "make all        Clean, install, and run all tests"

test:
	pytest tests/ -v

validate:
	python3 -m aeo_graph_engine.cli --test

install:
	pip install -e .

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache/ htmlcov/ .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

all: clean install validate test
