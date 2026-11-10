#!/usr/bin/env bash
# Pipeline completo y reproducible: datos reales → modelo → evaluación → app
set -e
python -m cafe.data_download --desde 2022-01-01
python -m cafe.data_prep
python -m cafe.risk_model
python -m cafe.evaluate_agent --mock
streamlit run app.py
