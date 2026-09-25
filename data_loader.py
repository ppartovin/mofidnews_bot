"""Utilities for loading the application's JSON data."""

import json
from pathlib import Path
from typing import Any


DATA_FILE = Path(__file__).with_name("datas.json")


def load_data(file_path: Path = DATA_FILE) -> Any:
    """Load and return JSON data from the configured data file."""
    try:
        with file_path.open("r", encoding="utf-8") as data_file:
            return json.load(data_file)
    except FileNotFoundError as error:
        raise RuntimeError(f"Data file was not found: {file_path}") from error
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Data file contains invalid JSON: {file_path}") from error
