# torgstat-analytics-case
Data analysis case for eCommerce: SQL funnel, metrics dashboard, Yandex.Metrica recommendations.

# Torgstat Analytics Case

## 📌 Контекст
Анализ данных онлайн-магазина для построения воронки, расчёта ключевых метрик и настройки аналитики.

## 📂 Структура проекта
- `data/` — входные данные (events.csv, invoices.csv, plans.csv, sessions.csv, subscriptions.csv, users.csv, сгенерированы скриптом scripts/generate_data.py)
- `sql/` — SQL-запросы для построения воронки
- `notebooks/` — Python ноутбуки для расчёта метрик
- `images/` — графики и скриншоты дашборда
- `report/` — итоговый PDF-отчёт с выводами

## 🔹 Задания
1. SQL-воронка по когортам
2. DAU / WAU / MAU, Retention Rate, LTV, CR
3. Настройка целей и UTM в Яндекс.Метрике

## 📊 Результаты
- **Retention Rate**: ...
- **LTV**: ...
- **CR**: ...

## 🛠 Стек
- SQL (PostgreSQL)
- Python (Pandas, Matplotlib)
- Tableau / Metabase
