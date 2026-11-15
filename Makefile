# Enterprise Data Governance & Quality Platform — Makefile (oss profile)
#
# The oss profile is standard-library Python + pytest and runs with no cloud
# account. `make pull` / `make bootstrap` is a one-time image pull for the local
# OpenMetadata demo and sits OUTSIDE the `make demo` 15-minute clock.

PYTHON ?= python3
export PYTHONPATH := src

.PHONY: help bootstrap pull validate test quality scorecard steward labels demo report clean

help:
	@echo "Targets:"
	@echo "  bootstrap  one-time: pull demo images (outside the demo clock)"
	@echo "  pull       alias for bootstrap"
	@echo "  validate   structurally validate ODCS contracts + governance files"
	@echo "  test       run the pytest suite (the oss quality engine)"
	@echo "  quality    run the data-quality gate over the synthetic extracts"
	@echo "  scorecard  print the KPI scorecard (placeholders unless a run file exists)"
	@echo "  steward    demo the steward issue/cleanse loop (fail -> issue -> cleanse -> re-run)"
	@echo "  labels     export the AI-FIT-01 label pack"
	@echo "  demo       run the full demo script (oss, under 15 min after image pull)"
	@echo "  report     build the PDF case-study pack (Phase 8; placeholder until then)"

bootstrap:
	@echo "One-time image pull for the local OpenMetadata demo."
	@echo "Requires Docker; this step is outside the 'make demo' clock."
	@if command -v docker >/dev/null 2>&1; then \
		docker compose pull || echo "compose pull skipped"; \
	else \
		echo "docker not found; oss tests and quality gate do not need it"; \
	fi

pull: bootstrap

validate:
	$(PYTHON) -m dgqp.cli validate

test:
	$(PYTHON) -m pytest

quality:
	$(PYTHON) -m dgqp.quality_cli

scorecard:
	$(PYTHON) -m dgqp.cli scorecard

steward:
	$(PYTHON) -m dgqp.workflow_cli

labels:
	$(PYTHON) -m dgqp.labels

demo:
	$(PYTHON) -m dgqp.demo

report:
	$(PYTHON) -m dgqp.report

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
