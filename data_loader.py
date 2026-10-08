"""Utilities for loading the application's JSON data."""

import json
from pathlib import Path
from typing import Any


DATA_FILE = Path(__file__).with_name("datas.json")
CLASSES_FILE = Path(__file__).with_name("classes_table.json")


def load_data(file_path: Path = DATA_FILE) -> Any:
    """Load the application data and class schedules for the AI assistant."""
    classes_file = file_path.with_name(CLASSES_FILE.name)
    return {
        "application_data": _load_json(file_path),
        "classes_table": _load_json(classes_file),
    }


def _load_json(file_path: Path) -> Any:
    """Load one JSON file and report configuration errors consistently."""
    try:
        with file_path.open("r", encoding="utf-8") as data_file:
            return json.load(data_file)
    except FileNotFoundError as error:
        raise RuntimeError(f"Data file was not found: {file_path}") from error
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Data file contains invalid JSON: {file_path}") from error
