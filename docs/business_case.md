# Torgstat Analytics: бизнес-кейс и легенда проекта

## Executive Summary

`Torgstat Analytics` — учебный end-to-end analytics engineering и Power BI
проект для вымышленного B2B SaaS-сервиса. Его основная бизнес-задача — дать
руководству и Finance единую картину billing и клиентской базы, а операционным
командам — возможность проследить проблему качества данных до конкретной строки
источника.

Проект сознательно моделирует работу не «с чистого листа». Аналитик приходит в
существующий продукт, получает CSV-extracts из нескольких логических source
domains, PostgreSQL, dbt-модели и незавершённый Power BI report. Его задача —
разобраться в grain, согласовать KPI, проверить расчёты, развить dashboard и
организовать воспроизводимый выпуск изменений через Git.

Текущий проект уже показывает полный технический путь:

```text
Source extracts
    → raw PostgreSQL
    → dbt staging
    → dbt marts
    → Power BI semantic model
    → report pages
    → data-quality handoff
```

При этом проект не должен называться production-системой. Данные синтетические,
MRR/ARR и recognized revenue ещё не реализованы, часть финансовых правил имеет
статус `DRAFT`, а несколько DAX-определений требуют исправления.

## 1. Каноническая легенда компании

### 1.1. Продукт

`Torgstat` — вымышленный облачный B2B SaaS-сервис аналитики. Компании создают
в нём рабочее пространство, приглашают сотрудников, просматривают dashboards и
выгружают данные.

Главная клиентская единица — `workspace`, то есть компания-аккаунт. Финансовые
отношения принадлежат workspace, а не отдельному пользователю.

### 1.2. Клиенты и тарифы

Клиенты представлены тремя сегментами:

- `smb`;
- `mid_market`;
- `enterprise`.

Продукт имеет четыре тарифа:

| Plan | Monthly price | Annual price | Бизнес-смысл |
| --- | ---: | ---: | --- |
| Free | 0 | 0 | Знакомство с продуктом, invoice не создаётся |
| Starter | 29 | 290 | Базовый платный тариф |
| Pro | 79 | 790 | Расширенные возможности |
| Enterprise | 249 | 2 490 | Крупные команды |

Числовая цена интерпретируется в billing currency workspace. В модели
используются EUR, GBP и USD.

### 1.3. Клиентский путь

```text
Компания создаёт workspace
        ↓
Создаётся owner и приглашаются users
        ↓
Sessions фиксируют first-touch acquisition source
        ↓
Workspace начинает с Free или подключает paid plan
        ↓
Создаётся subscription
        ↓
Upgrade/downgrade сохраняет subscription_id
        ↓
Monthly/annual billing создаёт invoices
        ↓
Payment status и paid_at отражают оплату
        ↓
Product events показывают использование сервиса
        ↓
Power BI связывает billing, customer и usage signals
```

Workspace может существовать без subscription. Это нормальная стадия customer
funnel, а не ошибка данных.

## 2. Проблема бизнеса

До появления аналитического контура разные команды видят только свой участок:

- Finance и Billing работают со счетами и оплатами;
- Product видит users, sessions и events;
- Growth анализирует acquisition source;
- Customer Success работает с отдельными customer accounts;
- ERP/source owners исправляют ошибки в исходных записях;
- руководство получает несогласованные показатели из разных выгрузок.

Из этого следуют типичные риски:

- разные определения «revenue» и «paid customer»;
- потеря или умножение строк на join;
- смешение billed amount, cash collection и recognized revenue;
- неполное валютное покрытие;
- dashboard показывает проблему, но не даёт business ID для исправления;
- изменение отчёта невозможно нормально проверить или воспроизвести.

## 3. Миссия аналитического продукта

Создать единую, проверяемую и воспроизводимую аналитическую систему, которая:

1. показывает billing health и customer scale;
2. объясняет, какие планы, сегменты и страны формируют billed amount;
3. связывает acquisition и usage с клиентской и финансовой картиной;
4. отделяет корректные финансовые строки от DQ-исключений без удаления raw data;
5. позволяет пройти от KPI до `invoice_id`, `workspace_id`, batch и source row;
6. хранит semantic model и report definitions в Git;
7. даёт evidence для code review, UAT и release.

## 4. Project Charter

| Поле | Определение |
| --- | --- |
| Product owner | Head of Finance / Business Operations |
| Primary users | Leadership, Finance, Billing Operations |
| Secondary users | Growth, Product, Customer Success, Data/ERP owners |
| Delivery team | Analytics Engineer, BI Developer, Data Platform Engineer |
| Primary grain | Workspace для customer/financial decisions |
| Reporting currency | USD после контролируемой FX conversion |
| Primary reporting date | Invoice `issued_at` для текущего billing-led report |
| Review cadence | Weekly operational review и monthly business review |
| Current data window | 1 января 2023 — 31 мая 2024 |
| Release artifact | dbt marts + PBIP/TMDL/PBIR + validation evidence |
| Success condition | KPI воспроизводится SQL, фильтруется ожидаемо и раскрывается до source row |

## 5. Логические source domains

Физически учебные данные создаются генератором и передаются через CSV. Для
реалистичной работы каждый набор следует воспринимать как extract отдельного
корпоративного домена.

| Source domain | Сущности | Что имитируется |
| --- | --- | --- |
| SaaS application database | workspaces, users | Customer accounts и access model |
| Subscription service | subscriptions, plan history | Lifecycle договора и смена plan |
| Billing / ERP | plans, invoices | Product catalog, счета и payment lifecycle |
| Product analytics | sessions, events | Acquisition attribution и usage |
| External FX provider | fx_rates | Конвертация source currency в USD |

Это логическая легенда, а не утверждение о наличии реальных ERP/API-коннекторов.

## 6. Stakeholders и решения

| Stakeholder | Регулярный вопрос | Решение после анализа |
| --- | --- | --- |
| CEO / Leadership | Растёт ли billed amount и customer base? | Пересмотреть приоритет сегмента или коммерческий фокус |
| Finance lead | Все ли суммы корректны и покрыты FX? | Сертифицировать период или остановить публикацию |
| Billing Operations | Почему снизился payment success? | Исследовать failed/pending invoices |
| Product lead | Совпадает ли usage с развитием subscriptions? | Разобрать низкое adoption по segment/workspace |
| Growth lead | Какие acquisition sources приводят качественные accounts? | Перераспределить каналовый фокус |
| Customer Success | Что происходит с конкретным workspace? | Подготовить customer intervention |
| ERP / source owner | Какие записи требуют исправления? | Исправить source record и подтвердить следующим load |
| Analytics Engineering | Можно ли доверять модели и report? | Выпустить, заблокировать или отправить на доработку |

## 7. Бизнес-вопросы первой версии

Первая версия должна отвечать на следующие вопросы:

1. Какой объём корректных оплаченных invoices был выставлен по месяцам?
2. Как меняются invoice count, billed amount и payment success?
3. Какие plans, billing frequencies, countries и segments формируют сумму?
4. Сколько workspace имеют active paid subscription?
5. Какие acquisition sources связаны с paid customer outcomes?
6. Согласуется ли product usage с customer/subscription health?
7. Какие DQ issues влияют на доверие к финансовой отчётности?
8. Какие конкретные records нужно передать владельцу source system?

## 8. KPI Framework

### 8.1. Primary outcome KPIs

#### Eligible Paid Invoice Net USD (by issue date)

- Бизнес-смысл: net amount корректных оплаченных invoices, приведённый к USD.
- Grain: invoice, затем агрегация по workspace/period.
- Date: `issued_at`.
- Исключения: missing currency, negative amount, reconciliation mismatch,
  invalid billing/due/payment lifecycle, отсутствующий FX.
- Текущая техническая мера: `Net Revenue USD`.
- Статус: `IMPLEMENTED`, но название требует уточнения.

Безопасное бизнес-название —
`Eligible Paid Invoice Net USD (by issue date)`: мера включает только
analytics-eligible invoices со статусом `paid`, группирует их по `issued_at` и
не является ни cash collection по `paid_at`, ни бухгалтерским recognized
revenue.

#### Payment Success Rate

- Формула: paid invoices / all invoices в выбранном invoice-date context.
- Grain: invoice.
- Owner: Billing Operations.
- Решение: исследовать изменение failed/pending population.
- Статус: `IMPLEMENTED`.

#### Active Paid Workspaces

- Целевое определение: distinct workspaces с active subscription и non-Free
  действующим plan на выбранную as-of date.
- Grain: workspace as-of date.
- Owner: Finance / Commercial Operations.
- Статус: `NEEDS REVISION`.

Текущий DAX проверяет active subscription, но не исключает Free plan и не
реализует исторический as-of context.

### 8.2. Driver metrics

| Driver | Что объясняет | Статус |
| --- | --- | --- |
| Eligible Invoices | Размер финансово пригодной invoice population | Implemented |
| Paid Invoices | Числитель payment success | Implemented |
| Active Subscriptions | Текущий subscription base | Implemented |
| Paid plan mix | Вклад Starter/Pro/Enterprise | Partial |
| Workspace-to-paid conversion | Переход созданного workspace в paid | Planned |
| Sessions by session date | Acquisition/engagement trend | Implemented |
| Events by event date | Product activity trend | Implemented |
| Events per active workspace | Usage intensity | Needs date-context review |

### 8.3. Trust guardrails

| Guardrail | Release rule | Owner |
| --- | --- | --- |
| FX Coverage Rate | 100% для certified USD billed amount | Finance/Data |
| Invoice Amount Mismatch | Каждая строка имеет invoice ID и owner handoff | Billing/ERP |
| Missing Invoice Currency | Не скрывать; исключить из certified amount до решения | Billing/ERP |
| Invalid User Created At | Сохранить raw и передать application owner | Product/Data |
| Missing User Country | Показать влияние на geographic segmentation | Product/Data |
| dbt tests | Все blocking tests должны пройти | Analytics Engineering |
| SQL ↔ Power BI reconciliation | Totals совпадают без фильтров и на control slices | BI/Finance |

### 8.4. Почему пока нет performance targets

Synthetic dataset не является историческим performance baseline. Поэтому
проект может иметь технические release thresholds, но не должен придумывать
коммерческие цели вроде «рост revenue 15%» или «payment success 98%».

Performance targets появляются только после:

1. согласования metric owner;
2. нескольких стабильных reporting periods;
3. объяснения сезонности и data incidents;
4. утверждения target на WBR/MBR.

## 9. Как создаётся бизнес-ценность

### 9.1. Единые определения

Finance, Product и Leadership используют один semantic model вместо отдельных
Excel/SQL-версий KPI.

### 9.2. Быстрая диагностика

Пользователь начинает с KPI, переходит к segment/workspace, затем к invoice и
source row. Это сокращает путь от вопроса до проверяемого evidence.

### 9.3. Контролируемая финансовая отчётность

Неисправная строка не удаляется. Она остаётся доступной для traceability, но не
попадает в certified billed amount.

### 9.4. Операционный Data Quality

Dashboard показывает не только count ошибок, но должен передавать:

```text
issue_code
entity_id
workspace_id
source_system
field_name
severity
detected_at
load_batch_id
owner_team
resolution_status
ticket_id
```

### 9.5. Управляемые изменения

PBIP/TMDL/PBIR, dbt SQL, tests и документация доступны в Git. Изменение можно
review, протестировать, связать с ticket и при необходимости отменить.

## 10. Operating Model

### Weekly operational review

Участники: Analytics Engineering, Finance, Billing Operations, Data owners.

Повестка:

1. pipeline freshness и failed tests;
2. FX coverage;
3. новые и unresolved DQ issues;
4. payment success movement;
5. изменения definitions/backlog;
6. owner и срок следующего действия.

### Monthly business review

Участники: Leadership, Finance, Product, Growth.

Повестка:

1. eligible paid invoice net amount и customer scale;
2. plan/segment/country mix;
3. acquisition и usage signals;
4. основные риски доверия к данным;
5. решения и изменения приоритетов.

## 11. Data Quality Remediation Loop

```text
Source defect appears
    → pipeline preserves the row
    → staging assigns a quality flag
    → mart excludes it only from certified KPI
    → Power BI exposes count and business ID
    → issue is assigned to source owner
    → source is corrected
    → next batch reloads the record
    → validation proves that the issue is resolved
```

Power BI является monitoring и routing layer. Исправление должно происходить в
source system, а не вручную внутри report.

## 12. Scope и честные границы

### CURRENT — реализовано

- deterministic source generation;
- PostgreSQL raw load с batch lineage;
- dbt staging, marts, contracts и tests;
- multi-currency invoice conversion;
- initial Executive Overview;
- QA Revenue Trace;
- initial Data Quality Monitor;
- PBIP/TMDL/PBIR в Git;
- статический и SQL reconciliation framework.

### TARGET — следующая рабочая очередь

- исправить семантику `Canceled Subscriptions`;
- согласовать `Open/Paid/Net Revenue` naming и population;
- корректно определить `Active Paid Workspaces`;
- завершить Revenue and Plans;
- построить Acquisition and Usage;
- построить Workspace Drill-Through;
- создать `mart_data_quality_issues`;
- добавить owner/status/SLA для remediation;
- перенести quality gates в CI;
- перенести PostgreSQL на учебный managed service.

### APPROVED, но ещё не реализовано

- recognized revenue allocation;
- MRR/ARR definitions.

Правила recognized revenue и MRR/ARR уже утверждены в
[`business_rules.md`](business_rules.md), но соответствующие dbt-модели,
меры и report visuals ещё не реализованы.

### DRAFT — требуется business owner

- invoice currency fallback на workspace currency;
- authoritative FX conversion date;
- as-of определение active paid customer.

### OUT OF SCOPE — нельзя заявлять как опыт

- реальный production SLA/HA;
- enterprise ERP integration;
- processing Visa/Mastercard;
- production incident on-call;
- secure enterprise Power BI distribution;
- real customer or financial data.

## 13. Известные semantic blockers

До заявления о certified dashboard нужно закрыть:

1. `Canceled Subscriptions` использует `canceled`, тогда как contract хранит
   `cancelled`.
2. `Open Net Revenue USD` структурно blank, потому что upstream analytics amount
   существует только для paid eligible invoices.
3. `Paid Workspaces` и `Active Paid Workspaces` не проверяют non-Free plan.
4. Некоторые session/event metrics не реагируют на общий date slicer без
   `USERELATIONSHIP`.
5. При FX coverage ниже 100% USD amount является неполным.

## 14. Definition of Business-Ready

Dashboard считается готовым к stakeholder review, если:

- metric owner и business question зафиксированы;
- grain, date, population, filters и exclusions описаны;
- dbt build и blocking tests проходят;
- row/key reconciliation между слоями проходит;
- SQL и DAX totals совпадают;
- date/plan/workspace filters проверены;
- каждый DQ count раскрывается до business ID;
- известные limitations видимы пользователю;
- UAT evidence приложено к pull request;
- документация обновлена в том же change set.

## 15. Как представлять проект

### Короткая версия

> Я развиваю end-to-end analytics platform для синтетического B2B SaaS. Она
> объединяет customer accounts, users, subscriptions, invoices, acquisition,
> product events и FX. PostgreSQL и dbt формируют проверяемые marts, Power BI
> даёт billing-led управленческий report, а Data Quality workflow позволяет
> пройти от KPI до source row и владельца исправления.

### Версия для собеседования

> Я вошёл в проект как Analytics Engineer / BI Developer не на этапе greenfield:
> существовали source extracts, dbt-модели и незавершённый PBIP. Я восстановил
> business context и grain, проверил lineage и финансовые формулы, добавил
> reconciliation gates, развил semantic model и report pages, а также оформил
> операционный DQ handoff. Все изменения проходят через business rule, contract,
> dbt tests, SQL-to-Power-BI validation и Git review.

### Чего не говорить

Нельзя говорить, что проект:

- обслуживает настоящую компанию;
- работает под production SLA;
- содержит реальные банковские транзакции;
- уже реализует recognized revenue, MRR или ARR;
- использует enterprise Power BI Service deployment.

Корректная формулировка: это самостоятельно построенный production-like
training case с синтетическими данными и честно обозначенными ограничениями.

## 16. Источники истины внутри репозитория

При конфликте документов используется следующий приоритет:

1. утверждённый `docs/business_rules.md`;
2. утверждённый `docs/data_contract.md`;
3. реализованный dbt SQL и tests;
4. `report/power_bi/semantic_model.md`;
5. Power BI TMDL/PBIR definitions;
6. `report_blueprint.md` как target design;
7. README как краткая навигация.

Если target blueprint расходится с реализацией, нужно явно писать `PLANNED`, а
не считать функцию существующей.
