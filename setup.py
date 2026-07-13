"""
Конфигурация пакета torgstat для установки через setuptools.

Этот модуль определяет метаданные и зависимости пакета torgstat,
который предназначен для работы с торговой статистикой и базами данных.

Attributes:
    name (str): Package name - 'torgstat'
    version (str): Package version - 0.1
    packages (list): List of packages discovered under 'src'
    package_dir (dict): Mapping between package names and directories
    install_requires (list): Install dependencies

Dependencies:
    - sqlalchemy: ORM for database work
    - python-dotenv: Load environment variables from .env files
    - psycopg2-binary: PostgreSQL adapter for Python
    - pandas: Data analysis and tabular processing library

Project structure:
    The project uses a source-layout structure under 'src/',
    which is a recommended practice for Python projects.
"""
from setuptools import setup, find_packages

setup(
    name="torgstat",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "sqlalchemy",
        "python-dotenv",
        "psycopg2-binary",
        "pandas",
    ],
)
