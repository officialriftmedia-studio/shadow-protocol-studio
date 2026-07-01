.PHONY: install create-video lint test clean

install:
	pip install -e .

create-video:
	python -m shadow_protocol.cli $(ARGS)

lint:
	ruff check agents/ shadow_protocol/ tests/
	ruff format --check agents/ shadow_protocol/ tests/

test:
	python -m pytest tests/ -v

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
