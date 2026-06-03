import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

collect_ignore = ["src/translator_test.py"]


def pytest_addoption(parser):
    parser.addoption(
        "--update-gold",
        action="store_true",
        default=False,
        help="update golden test expectation files",
    )
