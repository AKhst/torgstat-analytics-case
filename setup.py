"""
Конфигурация пакета torgstat для установки через setuptools.

Этот модуль определяет метаданные и зависимости пакета torgstat,
который предназначен для работы с торговой статистикой и базами данных.

Attributes:
    name (str): Название пакета - 'torgstat'
    version (str): Версия пакета - 0.1
    packages (list): Список пакетов, найденных в директории 'src'
    package_dir (dict): Соответствие между именами пакетов и директориями
    install_requires (list): Список зависимостей для установки

Зависимости:
    - sqlalchemy: ORM для работы с базами данных
    - python-dotenv: Загрузка переменных окружения из .env файлов
    - psycopg2-binary: Адаптер PostgreSQL для Python
    - pandas: Библиотека для анализа данных и работы с таблицами

Структура проекта:
    Проект использует структуру с исходным кодом в директории 'src/',
    что является рекомендуемой практикой для Python проектов.
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
