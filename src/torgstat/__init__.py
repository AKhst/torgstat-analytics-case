# torgstat/__init__.py

# Делаем основные вещи доступными сразу при импорте пакета
from .db import get_engine, DB_SCHEMA

# Можно добавить версии, конфиги и т.д.
__version__ = "0.1"
