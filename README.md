# SaaS Analytics Case (PostgreSQL + dbt + Power BI)

Учебно-практический проект, приближенный к реальной боевой задаче: построение аналитической витрины и отчётности на основе сырых данных о пользователях и подписках SaaS-сервиса.  

Проект демонстрирует полный цикл работы с данными:  
**генерация → хранение в PostgreSQL → моделирование (dbt) → аналитика (SQL/Python) → визуализация (Power BI).**

---

## 🎯 Цели проекта
- Смоделировать данные, похожие на реальные (регистрация, каналы привлечения, подписки, платежи, активность в приложении).  
- Развернуть их в PostgreSQL внутри Docker.  
- Построить пайплайн с разделением на слои (raw → staging → mart).  
- Реализовать ключевые метрики для маркетинга и продакта:  
  - CR по каналам привлечения  
  - Retention / Churn  
  - LTV по тарифам  
  - DAU/WAU/MAU  
- Подключить Power BI и собрать управленческую отчётность.  

---

## ⚙️ Технологии
- **PostgreSQL 15** (Docker Compose)
- **dbt-core** для трансформаций
- **Python (pandas, numpy)** — генерация данных, EDA
- **Power BI** — визуализация
- **VS Code + Jupyter Notebooks** — анализ, тестирование гипотез

---

## 📂 Структура данных

В схеме `analytics` в PostgreSQL лежат сырые данные:

- **users** — пользователи (id, дата регистрации, регион)  
- **sessions** — сессии и источники трафика (utm_source, utm_medium, utm_campaign)  
- **plans** — тарифные планы (Basic / Pro / Business)  
- **subscriptions** — подписки пользователей, статус (active/churned)  
- **invoices** — счета/платежи (сумма, даты, оплачен/нет)  
- **events** — действия в приложении (app_open, feature_a, feature_b)

---

## 🚀 Запуск

1. Клонировать проект:  
   git clone https://github.com/USERNAME/torgstat-analytics-case.git
   cd torgstat-analytics-case
2. Поднять PostgreSQL через Docker Compose:
   docker-compose up -d
3. Данные автоматически загрузятся из init/ и будут доступны в схеме analytics.
4. Проверить подключение:
   psql -h localhost -U appuser -d torgdb
   Password:  # вводишь пароль для appuser