#!/usr/bin/env bash
# Ejecutar en CPU de nube; no entrena un LLM.
set -euo pipefail
python -m cafe.verify_services
python -m cafe.fetch_corpus
python -m cafe.data_download --desde 2022-01-01 --hasta 2026-10-31
python -m cafe.data_prep
python -m cafe.risk_model
python -m cafe.evaluate_csp
python -m cafe.evaluate_agent --mock
python -m cafe.evaluate_agent
python -m cafe.check_delivery
