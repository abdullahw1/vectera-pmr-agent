"""Load local development credentials without overriding the caller's environment."""

import os
from pathlib import Path

from dotenv import load_dotenv


def load_environment(path=None):
    if os.getenv("PMR_LOAD_ENV", "1") == "0":
        return
    env_file = Path(path) if path is not None else Path(__file__).resolve().parents[1] / ".env"
    # Preserve externally supplied evaluation keys and literal credential contents.
    load_dotenv(env_file, override=False, interpolate=False)
