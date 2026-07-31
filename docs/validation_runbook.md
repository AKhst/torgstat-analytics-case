# Сквозная проверка корректности данных и Power BI

Этот runbook отвечает не на вопрос «файл открывается?», а на более строгий
вопрос: **можно ли проследить каждую цифру от Power BI до исходной строки и
получить тот же результат независимым расчётом?**

## 1. Что означает «всё работает корректно»

Для этого проекта нужны шесть разных доказательств:

| Уровень | Что доказываем | Основная проверка |
| --- | --- | --- |
| Generator / CSV | Создан ожидаемый воспроизводимый набор | фиксированные row counts и внутренние Python-проверки |
| Raw | Все файлы загружены одним полным batch | batch ID, timestamp и source row lineage |
| Staging | Строки типизированы и помечены, но не потеряны | dbt contracts/tests и raw-to-staging parity |
| Marts | Join, фильтры, FX и агрегации не исказили данные | dbt tests и независимый SQL reconciliation |
| Semantic model | Relationships и DAX используют правильный grain/filter context | PBIP validator и SQL-to-DAX tie-out |
| Report | Slicers и visual interactions дают ожидаемый контекст | ручной сценарий в Power BI |

Один зелёный тест не заменяет остальные. Например, структурный PBIP validator
может доказать, что мера записана в допустимом TMDL-формате, но не может доказать,
что бизнес-смысл этой меры верен.

## 2. Текущий уровень доверия

На момент составления runbook:

- статические unit-тесты и PBIP validator проходят;
- модель содержит dbt contracts, generic tests и 9 singular business-rule tests;
- добавлен независимый SQL-аудит `scripts/validate_end_to_end.sql`;
- фактический runtime-аудит нужно выполнять на Mac при работающем PostgreSQL;
- финансовые показатели нельзя считать окончательно business-certified, пока
  правило invoice currency fallback и authoritative FX date остаются `DRAFT`.

Кроме того, статический аудит выявил несколько смысловых вопросов Power BI,
перечисленных в разделе 8. Они не исправляются автоматически этим runbook:
сначала нужно утвердить ожидаемое определение показателя.

## 3. Полная автоматическая проверка на Mac

Запустите Docker Desktop, затем в Terminal:

```bash
cd /path/to/torgstat-analytics-case
git status --short --branch
./scripts/run_local_pipeline.sh --skip-fx
```

Используйте `--skip-fx`, только если `data/fx_rates.csv` уже существует и его
происхождение вам известно. Для получения курсов заново:

```bash
./scripts/run_local_pipeline.sh
```

Важно: текущий `dbt source freshness` проверяет время загрузки raw. При
`--skip-fx` старый FX-файл получает новый `_loaded_at_utc`, поэтому зелёная
freshness сама по себе не доказывает свежесть или provenance курсов провайдера.
До добавления FX manifest это отдельная ручная проверка.

Pipeline выполняет:

1. запуск PostgreSQL и health check;
2. генерацию и внутреннюю проверку CSV;
3. получение или повторное использование FX;
4. транзакционную загрузку raw;
5. `dbt source freshness`;
6. `dbt build`;
7. независимый SQL reconciliation;
8. статическую проверку PBIP/TMDL/PBIR.

Успешный итог должен содержать одновременно:

```text
Completed successfully
FINAL RESULT: PASS - all automated SQL checks passed.
Power BI project structure is valid.
```

Если нужно повторить только dbt и SQL-аудит без перегенерации raw:

```bash
cd /path/to/torgstat-analytics-case
set -a
source .env
set +a

.venv/bin/python -m dbt.cli.main debug \
  --project-dir torgstat_dbt \
  --profiles-dir torgstat_dbt

.venv/bin/python -m dbt.cli.main source freshness \
  --project-dir torgstat_dbt \
  --profiles-dir torgstat_dbt

.venv/bin/python -m dbt.cli.main build \
  --project-dir torgstat_dbt \
  --profiles-dir torgstat_dbt

docker compose exec -T postgres \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -v raw_schema="$RAW_SCHEMA" \
  -v staging_schema="$STAGING_SCHEMA" \
  -v marts_schema="$MARTS_SCHEMA" \
  < scripts/validate_end_to_end.sql
```

SQL-аудит завершается кодом `1`, если хотя бы одна обязательная проверка имеет
статус `FAIL`. Поэтому его можно использовать как quality gate в CI/CD.

## 4. Что именно проверяет SQL-аудит

### Generator / raw

- фиксированные объёмы seed-42 dataset;
- непустой FX-набор;
- один `_load_batch_id` и один `_loaded_at_utc` для всех raw-таблиц;
- непрерывные и уникальные `_source_row_number`.

Точные baseline-объёмы:

| Таблица | Ожидается |
| --- | ---: |
| workspaces | 200 |
| plans | 4 |
| users | 2 500 |
| sessions | 1 297 |
| subscriptions | 180 |
| subscription_plan_history | 234 |
| invoices | 935 |
| events | 5 000 |

Если генератор намеренно меняется, эти baseline-значения нужно обновить в одном
коммите вместе с `data/README.md`, тестами и описанием причины.

### Raw → staging

Для каждой из девяти таблиц сравнивается row count. В staging плохая строка
должна получить quality flag, а не исчезнуть незаметно.

### Staging → marts

Проверяется сохранение строк через все `inner join`, один converted row на
invoice и непрерывность `dim_date`. Это закрывает типичную проблему, когда dbt
build зелёный, но корректная по SQL модель случайно потеряла строки из-за join.

### Финансовая логика

Независимо пересчитываются:

- формула `is_analytics_eligible`;
- null/non-null поведение analytics amounts;
- положительность FX и quote currency;
- FX coverage;
- правило latest FX date not after `period_start`;
- USD amounts из source amount × selected rate;
- каждая строка `mart_workspace_monthly_billing`.

Проверка доказывает, что код реализует записанную формулу. Она не превращает
`DRAFT`-правило в утверждённое бизнес-правило.

## 5. Сверка SQL с Power BI

После зелёного Mac pipeline на Windows:

```powershell
cd C:\Users\PBI_user\Desktop\PBI_project\torgstat-analytics-case
$macHostName = "YOUR_MAC_LOCAL_HOSTNAME.local"
Test-NetConnection $macHostName -Port 5433
Start-Process ".\report\power_bi\TorgstatAnalytics.pbip"
```

Продолжайте только при:

```text
TcpTestSucceeded : True
```

В Power BI:

1. Проверьте параметр
   `Server = YOUR_MAC_LOCAL_HOSTNAME.local:5433`.
2. Выполните `Home → Refresh`.
3. Очистите все slicers и filters.
4. Сравните KPI-карточки с блоком
   `Power BI reconciliation baseline (no report filters)` из SQL-аудита.
5. Сравните месячный график с блоком
   `Power BI monthly revenue baseline`.

Сначала сравнивайте без фильтров, затем повторите три среза:

- один `invoice month`;
- один `plan`;
- один `workspace`.

Для каждой сверки фиксируйте:

```text
count(invoice_key)
sum(analytics_net_amount_usd)
sum(analytics_tax_amount_usd)
sum(analytics_gross_amount_usd)
```

Для контрольного среза выполните в PostgreSQL тот же фильтр независимо от
Power BI. Замените значения в угловых скобках:

```sql
with filtered_invoices as (
    select *
    from marts.fct_invoices_converted
    where issued_at between date '<FROM_YYYY-MM-DD>' and date '<TO_YYYY-MM-DD>'
      and plan_id = <PLAN_ID>
      and workspace_id = '<WORKSPACE_ID>'
)
select
    count(distinct invoice_key) as invoices,
    count(distinct invoice_key)
        filter (where is_analytics_eligible) as eligible_invoices,
    sum(analytics_net_amount_usd) as net_revenue_usd,
    sum(analytics_tax_amount_usd) as tax_revenue_usd,
    sum(analytics_gross_amount_usd) as gross_revenue_usd
from filtered_invoices;
```

Для проверки только одного измерения удалите две ненужные строки фильтра.
Затем установите точно такие же date/plan/workspace filters в Power BI.

Небольшое расхождение отображения из-за округления допустимо только на экране.
SQL/DAX totals до форматирования должны совпадать.

## 6. Проверка одной цифры до исходной строки

Для revenue выберите один invoice на странице `QA Revenue Trace` и пройдите путь:

```text
Power BI fct_invoices_converted[invoice_id]
  → marts.fct_invoices_converted
  → marts.fct_invoices
  → staging.stg_invoices
  → raw.invoices
  → data/invoices.csv
```

В PostgreSQL:

```sql
select *
from marts.fct_invoices_converted
where invoice_id = <INVOICE_ID>;

select *
from staging.stg_invoices
where invoice_id = <INVOICE_ID>;

select *
from raw.invoices
where invoice_id = <INVOICE_ID>;
```

Для исходного файла используйте `source_file_name` и `source_row_number`.
Повторите trace минимум для:

- одного корректного paid invoice;
- одного amount mismatch;
- одного missing currency или failed invoice.

Так проверяется не только итог, но и объяснимость исключения строки из KPI.

## 7. Проверка Data Quality Monitor

Для каждого DQ KPI должен существовать детальный список business IDs:

| KPI | Ключ для передачи владельцу данных | Обязательные поля |
| --- | --- | --- |
| Missing Invoice Currency | `invoice_id` | workspace, subscription, issue date, source row |
| Invoice Amount Mismatch | `invoice_id` | net, tax, gross, difference, source row |
| Invalid User Created At | `user_id` | raw timestamp, workspace, source row |
| Missing User Country | `user_id` | workspace, role, source row |
| FX Coverage | `invoice_id` | currency, period_start, selected FX date/rate |

Проверьте visual interactions:

1. Выберите категорию/столбец mismatch.
2. Детальная таблица должна оставить только соответствующие invoices.
3. Выберите одну строку и убедитесь, что ID находится в SQL и raw.
4. Очистите выбор и повторите для missing currency.

Карточка Power BI сама по себе обычно не является фильтром. Для управляемого
drill-down используйте bar/table visual, visual-level filter, drill-through или
отдельную detail-страницу.

## 8. Известные смысловые вопросы, блокирующие полную сертификацию

### `Canceled Subscriptions`

Текущий DAX фильтрует значение `canceled`, а staging/contract используют
`cancelled`. Текущая мера поэтому возвращает 0/blank для валидных данных.

### `Paid Net Revenue USD` и `Open Net Revenue USD`

Upstream `is_analytics_eligible` уже требует `payment_status = 'paid'`.
Следовательно:

- `Paid Net Revenue USD` совпадает с `Net Revenue USD`;
- `Open Net Revenue USD` структурно blank.

Нужно решить, что именно требуется бизнесу: billed/open amount, cash collected
или eligible paid revenue. После решения следует согласованно изменить mart,
названия и DAX.

### `Paid Workspaces`

Текущие меры считают workspaces с subscriptions, но не доказывают наличие
платного plan. В dataset возможна Free subscription. Требуется утвердить grain и
дату показателя: current active paid, paid during selected period или ever paid.

### Date slicer

У invoice issue date активная relationship. У sessions/events date relationships
неактивны и должны включаться через `USERELATIONSHIP`. Поэтому меры на базе
обычных `Sessions`/`Events` могут не реагировать на общий date slicer.

### FX coverage

При coverage ниже 100% revenue SUM пропускает строки без конвертации, а Average
Invoice Net использует полный eligible denominator. Revenue KPI следует
публиковать только при `FX Coverage Rate = 100%` либо с явным предупреждением.

## 9. Evidence package после каждого значимого изменения

Для профессиональной приёмки сохраняйте:

```text
Git commit:
Environment:
Pipeline started/finished:
Raw load_batch_id:
Raw loaded_at_utc:
dbt source freshness result:
dbt build result:
SQL reconciliation result:
PBIP validator result:
Power BI refresh time:
SQL ↔ KPI comparison:
Tested slicers:
Known exceptions / approved decisions:
Reviewer:
```

Минимальный release gate:

- все automated checks `PASS`;
- `dbt source freshness` не имеет error;
- FX Coverage равен 100% для certified revenue;
- SQL и Power BI totals совпадают без фильтров и на трёх контрольных срезах;
- любой DQ count раскрывается до business ID и source row;
- известные смысловые вопросы либо исправлены, либо явно зафиксированы как
  approved limitation.

## 10. Как разбирать FAIL

| Где FAIL | Сначала смотреть |
| --- | --- |
| Generator baseline | seed, параметры генератора, `data/README.md` |
| Batch/row lineage | importer и неполную загрузку CSV |
| Raw-to-staging parity | фильтр или join, случайно добавленный в staging |
| Staging-to-mart parity | `inner join`, FK и отфильтрованные quality rows |
| Eligibility | primitive flags и порядок бизнес-условий |
| FX | currency, period_start, rate coverage и выбранную дату |
| Monthly billing | grain, group by и null currency |
| SQL PASS, PBI mismatch | Refresh, filters, relationship и DAX filter context |

Не «подгоняйте» expected value под текущий dashboard. Сначала найдите источник
расхождения, подтвердите бизнес-правило, затем меняйте код и baseline в одном PR.
