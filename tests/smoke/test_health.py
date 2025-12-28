import pytest
import requests
import os

def test_api_health():
    # In docker-compose, they use container names, 
    # but for local smoke test we assume ports are mapped
    url = os.getenv("API_HEALTH_URL", "http://localhost:8000/health")
    try:
        resp = requests.get(url)
        assert resp.status_code == 200
    except requests.exceptions.ConnectionError:
        pytest.skip(f"API not reachable at {url}")

def test_bot_health():
    url = os.getenv("BOT_HEALTH_URL", "http://localhost:8080/health")
    try:
        resp = requests.get(url)
        assert resp.status_code == 200
    except requests.exceptions.ConnectionError:
        pytest.skip(f"Bot not reachable at {url}")

def test_panel_health():
    url = os.getenv("PANEL_HEALTH_URL", "http://localhost:5173/health")
    try:
        resp = requests.get(url)
        assert resp.status_code == 200
    except requests.exceptions.ConnectionError:
        pytest.skip(f"Panel not reachable at {url}")
