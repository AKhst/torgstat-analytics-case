# Шпаргалка: Mac pipeline и Power BI в Windows VM

## Где что работает

- **Mac:** Docker, PostgreSQL, Python, генерация данных и dbt.
- **Windows VM:** Power BI Desktop, VS Code и рабочая копия Git.
- **Адрес PostgreSQL из Windows:** `MacBook-Pro-Aleksei.local:5433`.
- **База:** `torgdb`.

После обычного перезапуска Windows VM полный pipeline запускать не нужно. Если PostgreSQL на Mac уже работает, достаточно проверить порт и открыть PBIP.

## Обычный старт после перезапуска Windows VM

В Windows PowerShell:

```powershell
cd C:\Users\PBI_user\Desktop\PBI_project\torgstat-analytics-case
Test-NetConnection MacBook-Pro-Aleksei.local -Port 5433
git pull --ff-only
Start-Process ".\report\power_bi\TorgstatAnalytics.pbip"
```

Продолжать можно только при:

```text
TcpTestSucceeded : True
```

После открытия Power BI:

1. Если требуется, откройте `Home → Transform data → Edit parameters`.
2. Установите `Server = MacBook-Pro-Aleksei.local:5433`.
3. Оставьте `Database = torgdb`.
4. Используйте `READONLY_USER` и `READONLY_PASSWORD` из Mac `.env`.
5. Выполните `Apply changes → Refresh`.

Значение `localhost:5433` хранится в Git как переносимое значение по умолчанию. Локальное имя Mac не следует добавлять в публичный коммит.

## Если Windows не видит PostgreSQL

Если `TcpTestSucceeded` равен `False`, перейдите на Mac. Убедитесь, что Docker запущен, затем в Terminal:

```bash
cd /path/to/torgstat-analytics-case
docker compose up -d postgres
docker compose ps postgres
./check_postgres.sh
nc -vz localhost 5433
```

После этого снова в Windows:

```powershell
Test-NetConnection MacBook-Pro-Aleksei.local -Port 5433
```

Диагностика контейнера на Mac:

```bash
docker compose logs --tail=100 postgres
docker compose port postgres 5432
lsof -nP -iTCP:5433 -sTCP:LISTEN
```

Ожидаемая публикация Docker — `0.0.0.0:5433` или `*:5433`.

## Быстрый пересчёт данных на Mac

Используйте, когда изменились генератор, importer, dbt-модели или требуется пересоздать тестовые данные. Существующий файл FX будет использован повторно:

```bash
cd /path/to/torgstat-analytics-case
./scripts/run_local_pipeline.sh --skip-fx
```

Скрипт:

1. запускает PostgreSQL;
2. проверяет базу и роли;
3. заново генерирует CSV;
4. импортирует raw-таблицы;
5. выполняет `dbt build`;
6. проверяет структуру PBIP.

Импорт заменяет raw-таблицы, поэтому для обычного открытия отчёта этот запуск не нужен.

## Полный pipeline с обновлением FX

Используйте, когда необходимо повторно скачать исторические курсы валют:

```bash
cd /path/to/torgstat-analytics-case
./scripts/run_local_pipeline.sh
```

## Только dbt build

Если исходные данные уже загружены и изменились только dbt-модели:

```bash
cd /path/to/torgstat-analytics-case
set -a
source .env
set +a
.venv/bin/python -m dbt.cli.main build \
  --project-dir torgstat_dbt \
  --profiles-dir torgstat_dbt
```

После успешного `dbt build` выполните `Refresh` в Power BI.

## Проверка PBIP

На Mac:

```bash
.venv/bin/python -m unittest discover -s tests -p "test_validate_power_bi_project.py"
.venv/bin/python scripts/validate_power_bi_project.py
```

В Windows PowerShell:

```powershell
$env:UV_CACHE_DIR = "$env:TEMP\torgstat-uv-cache"
uv run --offline python -m unittest discover -s tests -p "test_validate_power_bi_project.py"
uv run --offline python scripts\validate_power_bi_project.py
```

Ожидаемый итог:

```text
OK
Power BI project structure is valid.
```

## Сохранение изменений Power BI в Git

Перед `git pull` закройте Power BI Desktop. После сохранения отчёта:

```powershell
cd C:\Users\PBI_user\Desktop\PBI_project\torgstat-analytics-case
git status
git diff --check
git diff
```

Проверьте, что персональный сервер не попадает в коммит:

```powershell
git diff -- ".\report\power_bi\TorgstatAnalytics.SemanticModel\definition\expressions.tmdl"
```

Затем добавьте только намеренные изменения, создайте коммит и отправьте его:

```powershell
git add <нужные-файлы>
git commit -m "Describe Power BI change"
git push
```

Не используйте `git add .`, пока не проверили `expressions.tmdl`, `.env` и остальные локальные настройки.

## Короткая памятка: с чего начинать

```text
Обычный день:
Windows Test-NetConnection → git pull → открыть PBIP → Refresh

Нет соединения:
Mac docker compose up → check_postgres.sh → Windows Test-NetConnection

Изменились dbt-модели:
Mac dbt build → Power BI Refresh

Нужно пересоздать все тестовые данные:
Mac run_local_pipeline.sh --skip-fx → Power BI Refresh

Нужно обновить ещё и курсы валют:
Mac run_local_pipeline.sh → Power BI Refresh
```
