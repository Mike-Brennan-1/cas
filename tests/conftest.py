import os

# Must be set before cas.config is imported. load_dotenv() doesn't override
# existing variables, so tests never read the real key and need no .env file.
os.environ["OPEN_AI_API_KEY"] = "test-key"

from datetime import date
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import streamlit as st
from PIL import Image

import cas.ai
import cas.sim_store


@pytest.fixture(autouse=True)
def fake_openai(monkeypatch):
    """Replace the shared OpenAI client so no test can reach the real API."""
    fake = MagicMock()
    fake.responses.create.return_value = SimpleNamespace(id="resp_1", output_text="A backstory")
    monkeypatch.setattr(cas.ai.client, "client", fake)
    cas.ai.client.reset_conversation()
    return fake.responses.create


@pytest.fixture(autouse=True)
def sims_dir(monkeypatch, tmp_path):
    """Send saves to a temp folder so tests never touch real saved sims."""
    path = tmp_path / "sims"
    path.mkdir()
    monkeypatch.setattr(cas.sim_store, "SIMS_DIR", path)
    return path


@pytest.fixture(autouse=True)
def clear_streamlit_cache():
    st.cache_data.clear()
    yield
    st.cache_data.clear()


@pytest.fixture
def png_bytes():
    buffer = BytesIO()
    Image.new("RGB", (2, 2), "red").save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def make_sim():
    """Build an object with the same fields as the sim class in app.py."""

    def _make_sim(**overrides):
        fields = {
            "first_name": "Terry",
            "surname": "Anderson",
            "dob": date(1990, 11, 6),
            "hometown": "Copperdale",
            "image": None,
            "traits": ["Creative", "Genius"],
            "aspiration": "Bestselling Author",
            "bonus_trait": "Poetic",
            "backstory": "Once upon a time",
        }
        return SimpleNamespace(**(fields | overrides))

    return _make_sim
