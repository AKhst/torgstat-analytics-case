# torgstat/__init__.py

# Expose core functionality directly when the package is imported
from .db import get_engine, DB_SCHEMA

# Versioning, configuration, and future extensions can be added here.
__version__ = "0.1"
