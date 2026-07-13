# 🏢 SaaS Analytics Platform (End-to-End DWH & BI)

Этот проект — симуляция полноценной аналитической платформы для SaaS-продукта. Он демонстрирует выстраивание надежного ELT-процесса с нуля: от имитации выгрузок из самописной ERP до слоистой архитектуры хранилища и версионируемой семантической модели в Power BI.

Главная цель проекта — показать подход **BI Tech Lead** к проектированию данных: обеспечение Data Quality, строгую изоляцию слоев (Medallion Architecture) и внедрение инженерных практик (CI/CD) в аналитику.

---

## 🎯 Архитектура и Решения
- **Слой извлечения (Extract):** Симуляция выгрузок "боевой ERP" в транзитную зону (CSV) с помощью Python.
- **Слой загрузки (Load):** Идемпотентный Python-скрипт загружает сырые данные в DWH в выделенную схему `raw` (Бронзовый слой).
- **Слой трансформации (Transform / dbt):** - `staging` (Серебро): Очистка, типизация и базовая нормализация.
  - `marts` (Золото): Построение витрин данных по схеме "Звезда" (Star Schema) для фактов (подписки, платежи) и измерений (пользователи, тарифы).
- **Слой BI (Power BI):** Использование подхода Golden Dataset (единая семантическая модель). Проект сохранен в формате `.pbip` для прозрачного версионирования DAX-мер и метаданных.
- **Автоматизация:** Заложена база для CI/CD проверки качества dbt-моделей и валидации отчетов.

---

## ⚙️ Стек технологий
- **Хранилище:** PostgreSQL 15 (Docker Compose)
- **ELT & Data Quality:** Python (pandas, SQLAlchemy)
- **Трансформации:** dbt-core
- **Визуализация:** Power BI Desktop (.pbip / TMDL)
- **Инфраструктура & CI/CD:** GitHub Actions, Bash-скрипты

---

## 📂 Структура DWH (PostgreSQL)

Внутри базы `torgdb` данные проходят строгий жизненный цикл по схемам:

1. **Схема `raw` (Сырые данные):**
   Точная копия транзакционных данных (users, sessions, plans, subscriptions, invoices, events).
2. **Схема `staging` (Очищенные данные):**
   Предварительно обработанные представления (views).
3. **Схема `marts` (Бизнес-витрины):**
   Таблицы фактов (`fact_invoices`, `fact_subscriptions`) и измерений (`dim_users`, `dim_plans`), готовые для подключения BI.

*Ключевые метрики в модели:* CR по каналам, Retention/Churn, LTV по когортам, DAU/WAU/MAU.

---

## 🚀 Быстрый запуск (Local Environment)

1. **Клонировать репозиторий и настроить окружение:** git clone [https://github.com/USERNAME/torgstat-analytics-case.git](https://github.com/USERNAME/torgstat-analytics-case.git)
    cd torgstat-analytics-case
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

2. **Настроить переменные:**
   Создать файл `.env` в корне проекта (см. `.env.example`) для безопасной передачи паролей.

3. **Поднять DWH:**
    docker-compose up -d
    ./check_postgres.sh
   *Скрипт `init.sh` автоматически создаст базу, схемы и раздаст права.*

4. **Сгенерировать сырые данные (имитация ERP):**
    python scripts/generate_data.py

5. **Загрузить данные в слой `raw`:**
    python scripts/import_to_postgres.py

6. **Собрать витрины через dbt:**
    dbt run 

7. **Аналитика:**
   Подключить Power BI к схеме `marts` (пользователь `readonly`) или открыть файл из папки `/report`.

---

## 🧪 Проверка развертывания с нуля

Чтобы убедиться, что инфраструктура поднимается автоматически одной кнопкой, выполните следующие шаги:

1. Убейте контейнер и удалите старые данные:
    docker-compose down
    sudo rm -rf postgres_data

2. Поднимите базу с чистого листа:
    docker-compose up -d

3. Проверьте создание схемы через скрипт инициализации:
    docker exec -it torgstat_postgres psql -U torgadmin -d torgdb -c "\dn"