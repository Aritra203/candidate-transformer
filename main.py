"""Root-level entry point to proxy execution to src/main.py.

Ensures that commands like 'python main.py' execute correctly from the root directory.
"""

import sys
from pathlib import Path

# Add root folder to sys.path to allow execution without PYTHONPATH issues
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from src.main import app

if __name__ == "__main__":
    app()
