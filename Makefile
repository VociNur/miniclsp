VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

env:
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt

install: env
	mkdir -p $(HOME)/.local/bin
	ln -sf $(CURDIR)/minic-lsp-launcher.sh $(HOME)/.local/bin/minic-lsp

