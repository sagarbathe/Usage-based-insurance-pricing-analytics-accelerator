#!/bin/bash
# startup.sh — Azure App Service startup command for Streamlit.
# Set this as the Startup Command in App Service Configuration → General settings.
# Azure exposes the expected port via WEBSITES_PORT (default 8000).

PORT="${WEBSITES_PORT:-8000}"

python -m streamlit run app.py \
    --server.port="$PORT" \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=true \
    --browser.gatherUsageStats=false
