"""
Tools to generate and manage Markdown notebooks.
"""

from .logs import LOG_NAME, setup_logging
from .notebook import Notebook

# Version of the tidynotes package
__version__ = "21.01.01"

setup_logging()
