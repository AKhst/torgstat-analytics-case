# Torgstat Analytics Project Playbook

Единая шпаргалка по ежедневной работе, диагностике, Git, Power BI, dbt, PostgreSQL, качеству данных и развитию проекта.

## 1. Карта системы

```text
Synthetic CSV
    ↓
Python importer
    ↓
PostgreSQL raw
    ↓
dbt staging
    ↓
dbt marts
    ↓
Power BI semantic model (TMDL)
    ↓
Power BI report (PBIR)
```

Текущая инфраструктура:

- Mac: Docker, PostgreSQL, Python, dbt и полный pipeline.
- Windows VM: Power BI Desktop, VS Code и Git.
- PostgreSQL из Windows: `MacBook-Pro-Aleksei.local:5433`.
- База: `torgdb`.
- Power BI project: `report/power_bi/TorgstatAnalytics.pbip`.

## 2. Золотой маршрут: обычный рабочий день

После запуска Windows VM полный pipeline не нужен.

В Windows PowerShell:

```powershell
cd C:\Users\PBI_user\Desktop\PBI_project\torgstat-analytics-case
Test-NetConnection MacBook-Pro-Aleksei.local -Port 5433
git pull --ff-only
Start-Process ".\report\power_bi\TorgstatAnalytics.pbip"
```

Работать с данными можно только при:

```text
TcpTestSucceeded : True
```

В Power BI:

```text
Home → Transform data → Edit parameters

Server   = MacBook-Pro-Aleksei.local:5433
Database = torgdb

Apply changes → Refresh
```

Если Power BI запрашивает авторизацию:

```text
Authentication method = Database
Username = READONLY_USER из Mac .env
Password = READONLY_PASSWORD из Mac .env
```

## 3. Как понять, что запускать

| Ситуация | Действие |
| --- | --- |
| Перезапустилась только Windows VM | Проверить порт, открыть PBIP, Refresh |
| PostgreSQL на Mac уже работает | Pipeline не запускать |
| PostgreSQL не отвечает | Поднять Docker/PostgreSQL на Mac |
| Изменились только визуалы | Сохранить Power BI, проверить diff, коммитить Report |
| Изменилась DAX-мера или relationship | Проверить SemanticModel и Report |
| Изменились только dbt-модели | Выполнить `dbt build`, затем Refresh |
| Изменились generator/importer/contracts | Запустить pipeline с `--skip-fx` |
| Нужно обновить курсы FX | Запустить полный pipeline |
| Изменилась структура источника | Пройти полный change workflow |

## 4. PostgreSQL на Mac

### Запуск и проверка

```bash
cd /path/to/torgstat-analytics-case
docker compose up -d postgres
docker compose ps postgres
./check_postgres.sh
nc -vz localhost 5433
```

### Логи и порт

```bash
docker compose logs --tail=100 postgres
docker compose port postgres 5432
lsof -nP -iTCP:5433 -sTCP:LISTEN
```

Ожидаемая публикация:

```text
0.0.0.0:5433
```

или:

```text
*:5433
```

### Подключение к psql внутри контейнера

```bash
cd /path/to/torgstat-analytics-case
set -a
source .env
set +a
docker exec -it torgstat_postgres \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

Полезные команды psql:

```sql
\dn
\dt raw.*
\dt staging.*
\dt marts.*
\du
\q
```

## 5. Pipeline

### Быстрый полный пересчёт без скачивания FX

Использовать после изменений generator, importer, contracts или исходных данных:

```bash
cd /path/to/torgstat-analytics-case
./scripts/run_local_pipeline.sh --skip-fx
```

Скрипт:

1. запускает PostgreSQL;
2. проверяет базу, схемы и пользователей;
3. генерирует CSV;
4. повторно использует существующий FX-файл;
5. заменяет raw-таблицы;
6. выполняет `dbt build`;
7. проверяет PBIP.

### Полный pipeline с обновлением FX

```bash
cd /path/to/torgstat-analytics-case
./scripts/run_local_pipeline.sh
```

Не запускать без необходимости: importer использует `DROP TABLE ... CASCADE` и пересоздаёт raw-слой.

## 6. dbt

### Подготовка окружения

```bash
cd /path/to/torgstat-analytics-case
set -a
source .env
set +a
```

### Полный build

```bash
.venv/bin/python -m dbt.cli.main build \
  --project-dir torgstat_dbt \
  --profiles-dir torgstat_dbt
```

### Build одной модели и downstream-зависимостей

```bash
.venv/bin/python -m dbt.cli.main build \
  --select model_name+ \
  --project-dir torgstat_dbt \
  --profiles-dir torgstat_dbt
```

### Build модели и upstream-зависимостей

```bash
.venv/bin/python -m dbt.cli.main build \
  --select +model_name \
  --project-dir torgstat_dbt \
  --profiles-dir torgstat_dbt
```

### Только тесты

```bash
.venv/bin/python -m dbt.cli.main test \
  --project-dir torgstat_dbt \
  --profiles-dir torgstat_dbt
```

### Проверка компиляции

```bash
.venv/bin/python -m dbt.cli.main compile \
  --project-dir torgstat_dbt \
  --profiles-dir torgstat_dbt
```

### dbt Docs

```bash
.venv/bin/python -m dbt.cli.main docs generate \
  --project-dir torgstat_dbt \
  --profiles-dir torgstat_dbt

.venv/bin/python -m dbt.cli.main docs serve \
  --project-dir torgstat_dbt \
  --profiles-dir torgstat_dbt
```

## 7. Power BI

### Открыть отчёт вручную

Путь:

```text
C:\Users\PBI_user\Desktop\PBI_project\torgstat-analytics-case\report\power_bi\TorgstatAnalytics.pbip
```

Или из PowerShell:

```powershell
Start-Process ".\report\power_bi\TorgstatAnalytics.pbip"
```

### Что хранится в Git

- `.pbip`: точка входа.
- `.pbir`: ссылка report → semantic model.
- `Report/definition/pages`: страницы и визуалы PBIR.
- `SemanticModel/definition/tables`: таблицы, меры и partitions TMDL.
- `relationships.tmdl`: связи.
- `expressions.tmdl`: параметры Server и Database.

### Правильное параметризованное подключение

```powerquery
PostgreSQL.Database(#"Server", #"Database")
```

Не коммитить hardcoded connection:

```powerquery
PostgreSQL.Database("personal-host", "torgdb")
```

### Правило сохранения

Power BI может автоматически:

- обновить версию PBIR schema;
- нормализовать JSON;
- добавить свойства formatting;
- записать локальный hostname;
- заменить параметры literal-значениями;
- оставить `PBI_ResultType = Exception` после неудачного Refresh.

Поэтому после каждого сохранения:

```powershell
git status
git diff --stat
git diff
```

Если изменялись только визуалы:

```powershell
git add ".\report\power_bi\TorgstatAnalytics.Report"
git diff --cached
```

Не добавлять весь SemanticModel автоматически.

## 8. Data Quality Monitor

DQ-страница должна отвечать на три вопроса:

1. Сколько проблем?
2. Какие записи проблемные?
3. Кому и с какими идентификаторами передать исправление?

### Пример: invoice amount mismatch

Мера:

```DAX
Invoice Amount Mismatch Count =
CALCULATE (
    [Invoices],
    fct_invoices_converted[has_amount_reconciliation_mismatch] = TRUE ()
)
```

Эта мера считает проблемы, но её внутренний фильтр не передаётся автоматически другой таблице.

Для detail table установить visual-level filter:

```text
fct_invoices_converted[has_amount_reconciliation_mismatch] = True
```

Для связи графика и таблицы:

```text
Select chart → Format → Edit interactions → table → Filter
```

Detail table должна содержать:

```text
invoice_id
workspace_id
issued_at
source_currency_code
net_amount
tax_amount
gross_amount
amount_reconciliation_difference
payment_status
quality flags
loaded_at_utc
```

### Путь расследования

```text
Power BI measure
    ↓
marts.fct_invoices_converted
    ↓
staging invoice model
    ↓
raw.invoices
    ↓
source CSV / ERP record
```

### Целевая production-модель качества

Создать `mart_data_quality_issues` с grain «одна строка — одна проблема»:

```text
issue_id
issue_code
entity_type
record_id
source_system
source_field
severity
detected_at_utc
load_batch_id
owner_team
status
ticket_id
resolved_at_utc
```

## 9. Проверка PBIP

### На Mac

```bash
.venv/bin/python -m unittest discover \
  -s tests \
  -p "test_validate_power_bi_project.py"

.venv/bin/python scripts/validate_power_bi_project.py
```

### В Windows

```powershell
$env:UV_CACHE_DIR = "$env:TEMP\torgstat-uv-cache"

uv run --offline python -m unittest discover `
  -s tests `
  -p "test_validate_power_bi_project.py"

uv run --offline python scripts\validate_power_bi_project.py
```

Ожидаемый результат:

```text
OK
Power BI project structure is valid.
```

## 10. Git: безопасный рабочий процесс

### Перед началом работы

Закрыть Power BI и выполнить:

```powershell
cd C:\Users\PBI_user\Desktop\PBI_project\torgstat-analytics-case
git status
git pull --ff-only
```

### Посмотреть изменения

```powershell
git status --short --branch
git diff --name-status
git diff --stat
git diff
git diff --check
```

### Проверить Power BI connection

```powershell
git diff -- `
  ".\report\power_bi\TorgstatAnalytics.SemanticModel\definition\expressions.tmdl"

git diff | Select-String "PostgreSQL.Database|PBI_ResultType|password|secret"
```

### Добавить только нужные файлы

```powershell
git add <точный-файл-или-папка>
git diff --cached --name-status
git diff --cached
```

### Commit и push

```powershell
git commit -m "Describe the business change"
git push origin main
```

### Если случайно выполнен `git add .`

Снять всё со staging, не удаляя рабочие изменения:

```powershell
git restore --staged .
```

### Сделать резервную копию локального diff

```powershell
git diff > C:\Users\PBI_user\Desktop\torgstat-local-backup.patch
```

### Отменить только незакоммиченные Power BI-изменения

Сначала закрыть Power BI и сохранить backup. Затем:

```powershell
git restore --worktree -- `
  ".\report\power_bi\TorgstatAnalytics.Report" `
  ".\report\power_bi\TorgstatAnalytics.SemanticModel"
```

Команда удаляет локальные незакоммиченные изменения указанных папок.

### Безопасно отменить уже опубликованный commit

```powershell
git revert <commit-sha>
git push
```

Не применять без отдельного решения:

```text
git reset --hard
git clean -fd
git push --force
```

## 11. Поиск по проекту

### Список файлов

```powershell
rg --files
```

### Найти текст

```powershell
rg -n "Invoice Amount Mismatch"
rg -n "PostgreSQL.Database" report\power_bi
rg -n "TODO|FIXME|placeholder"
```

### Найти Power BI параметры и меры

```powershell
rg -n "expression Server|expression Database" `
  report\power_bi\TorgstatAnalytics.SemanticModel

rg -n "^\tmeasure " `
  report\power_bi\TorgstatAnalytics.SemanticModel\definition\tables
```

## 12. Change workflow

Любое изменение структуры данных проходит цепочку:

```text
Business rule
→ Data contract
→ Generator
→ CSV validation
→ Importer contract
→ Raw source
→ Staging model
→ Mart model
→ Tests
→ dbt Docs
→ Power BI semantic model
→ Visualization
```

Перед реализацией ответить:

```text
Какой grain?
Кто владелец данных?
Как определяется metric?
Какие записи считаются невалидными?
Как изменение повлияет на историю?
Какая валюта и дата FX?
Какие downstream-модели затрагиваются?
Как проверить backward compatibility?
```

## 13. Definition of Done

### Для dbt-модели

- Grain определён.
- Primary/business keys проверены.
- Sources и contracts обновлены.
- SQL компилируется.
- `dbt build` проходит.
- Tests покрывают ключевые правила.
- Описание и lineage обновлены.
- Downstream Power BI проверен.

### Для DAX-меры

- Есть бизнес-определение.
- Определены numerator и denominator.
- Понятно поведение при blank/zero.
- Понятна используемая date relationship.
- Format string задан.
- Результат сверяется с detail rows.

### Для Power BI-страницы

- Понятен пользователь и решение.
- KPI имеют определения.
- Filters предсказуемы.
- Visual interactions проверены.
- Есть путь от агрегата к detail rows.
- Нет технической «простыни» без назначения.
- Нет hardcoded personal connection.
- PBIP validator проходит.

### Для commit

- `git diff` просмотрен.
- `git diff --cached` просмотрен.
- Нет `.env`, паролей и персонального connection.
- Нет `PBI_ResultType = Exception`.
- Tests и validators зелёные.
- Commit содержит одно логическое изменение.

## 14. CI/CD: целевая защита

### На Pull Request

Автоматически выполнять:

```text
Python unit tests
PBIP/TMDL/PBIR validation
JSON parsing
Measure formatString checks
Relationship reference checks
Visual field reference checks
Forbidden secret/connection checks
dbt compile or parse
```

Запрещать:

```text
hostname:5433:5433
hardcoded PostgreSQL.Database("host", "database")
PBI_ResultType = Exception
.env
passwords and connection strings
```

### На main

Первое время:

- CI validation запускается автоматически.
- Cloud data deployment запускается вручную через `workflow_dispatch`.
- Secrets находятся в GitHub Secrets.
- Host, port и database находятся в GitHub Variables.
- Destructive raw reload не запускается на каждый commit.

## 15. Стратегия развития проекта

### Этап 0. Стабилизация локального проекта

Цель: получать повторяемый чистый результат.

- Сохранить параметризованные Power Query partitions.
- Не коммитить personal hostname.
- Усилить PBIP validator.
- Добавить проверки hardcoded connections и exception annotations.
- Довести Data Quality detail tables до actionable-состояния.

### Этап 1. CI quality gate

Цель: плохое изменение не попадает в `main`.

- Добавить GitHub Actions workflow.
- Запускать tests и static validation на PR.
- Включить required status check.
- Добавить secret scanning.
- Разделить business changes и автоматическую PBIR normalization.

### Этап 2. Managed PostgreSQL

Цель: убрать зависимость от включённого Mac.

- Создать учебный managed PostgreSQL, например Aiven Free.
- Использовать стабильный DNS и TLS.
- Создать отдельные pipeline и read-only BI roles.
- Добавить `POSTGRES_SSLMODE`.
- Создать cloud bootstrap для schemas и grants.
- Выполнить importer и `dbt build`.
- Подключить Power BI к cloud endpoint.

Бесплатный managed service остаётся demo-средой: он не даёт полноценный SLA, HA и корпоративную сеть.

### Этап 3. Cloud pipeline

Цель: воспроизводимый deployment данных.

- Отделить local Docker startup от cloud pipeline.
- Добавить ручной GitHub Actions deployment.
- Хранить credentials в GitHub Secrets.
- Сохранять артефакты dbt Docs.
- Добавить freshness и reconciliation checks.
- Перейти от `DROP TABLE ... CASCADE` к контролируемой загрузке.

### Этап 4. Завершение BI

Цель: цельный аналитический продукт.

- Доработать Executive Overview.
- Создать Revenue and Plans.
- Создать Acquisition and Usage.
- Создать Workspace Drill-Through.
- Завершить Data Quality Monitor.
- Добавить tooltips, navigation и consistent slicers.
- Зафиксировать metric definitions.

### Этап 5. Operational Data Quality

Цель: не только видеть ошибку, но и управлять исправлением.

- Создать `mart_data_quality_issues`.
- Ввести severity, owner и SLA.
- Добавить detected/resolved lifecycle.
- Связать issue с source record и load batch.
- Добавить статус remediation и ticket ID.
- Проверять исправление следующим pipeline run.

### Этап 6. Production-like governance

Цель: показать зрелый инженерный процесс.

- Разделить dev/test/prod environments.
- Применить least privilege.
- Добавить TLS и rotation credentials.
- Добавить backups/restore test.
- Добавить monitoring и alerting.
- Документировать release и rollback.
- Запретить прямые изменения production data.

## 16. Ближайший практический backlog

Приоритет P0:

1. Усилить `validate_power_bi_project.py`.
2. Добавить CI workflow.
3. Сделать invoice mismatch table предфильтрованной.
4. Проверить visual interactions.
5. Убрать неинформативные detail tables.

Приоритет P1:

1. Создать `mart_data_quality_issues`.
2. Завершить Executive Overview.
3. Создать Revenue and Plans.
4. Создать Acquisition and Usage.
5. Создать Workspace Drill-Through.

Приоритет P2:

1. Перенести PostgreSQL в managed service.
2. Добавить TLS/cloud config.
3. Перенести pipeline в ручной GitHub Actions workflow.
4. Добавить monitoring, backups и deployment documentation.

## 17. Как рассказывать о проекте

Короткое описание:

> Построен воспроизводимый analytics engineering pipeline для synthetic B2B SaaS: генерация контролируемых source data, PostgreSQL raw layer, dbt staging/marts, multi-currency financial metrics, data-quality controls и source-controlled Power BI PBIP/TMDL/PBIR.

Что проект доказывает:

- понимание grain и data contracts;
- dimensional modeling;
- dbt dependencies, tests и documentation;
- финансовые метрики и FX;
- Power BI semantic modeling;
- DAX и date relationships;
- BI as Code;
- data-quality monitoring;
- Git-based change control.

Что пока не заявлять:

- настоящий production SLA;
- реальный enterprise ERP integration;
- опыт Visa/Mastercard processing;
- production incident management;
- secure enterprise Power BI distribution.

## 18. Главное правило

```text
Сначала понять business rule и grain.
Потом изменить данные и dbt.
Потом проверить качество.
Только после этого менять Power BI.
Перед commit всегда смотреть staged diff.
```

Дополнительные документы:

- `docs/daily_runbook.md`
- `docs/change_workflow.md`
- `docs/data_contract.md`
- `docs/business_rules.md`
- `report/power_bi/README.md`
- `report/power_bi/semantic_model.md`
- `report/power_bi/report_blueprint.md`
