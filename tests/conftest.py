"""Test path setup for the standalone custom integration repository."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "custom_components"))
