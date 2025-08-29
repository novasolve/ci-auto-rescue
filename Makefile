SHELL := /bin/zsh
.PHONY: venv

# Set up a local Python virtual environment and install dependencies if available
venv:
	@echo "Creating .venv and installing dependencies (if any)"
	python3 -m venv .venv
	. .venv/bin/activate && python -m pip install --upgrade pip
	@if [ -f requirements.txt ]; then \
		. .venv/bin/activate && pip install -r requirements.txt; \
	fi
	@if [ -f demo-requirements.txt ]; then \
		. .venv/bin/activate && pip install -r demo-requirements.txt; \
	fi
	@if [ -f pyproject.toml ]; then \
		. .venv/bin/activate && pip install -e .; \
	fi
