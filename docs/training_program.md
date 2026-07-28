# Torgstat Analytics: программа реальной рабочей практики

## Цель тренажёра

Этот репозиторий используется как симуляция ежедневной работы Analytics
Engineer / BI Developer в B2B SaaS-команде.

Рабочая роль:

> Вы отвечаете за путь от business question и source data до проверенного KPI,
> dbt-модели, Power BI visual, UAT evidence и контролируемого release.

Проект специально начинается не с пустой папки. В нём уже есть pipeline,
business rules, dbt-модели, tests и незавершённый PBIP. Работа состоит в том,
чтобы разобраться в существующей системе, находить ограничения, безопасно
вносить изменения и объяснять результат бизнесу.

## 1. Условная команда

| Роль | Что запрашивает или проверяет |
| --- | --- |
| Head of Finance | Billing KPIs, FX coverage, invoice reconciliation |
| Billing Operations | Failed/pending invoices и source corrections |
| Revenue Operations | Plan, segment, country и paid customer analysis |
| Product / Growth | Acquisition, sessions и product events |
| Customer Success | Workspace 360 и customer-level investigation |
| ERP / Source Owner | Исправление конкретных source records |
| Data Platform Engineer | PostgreSQL, pipeline, access, CI и deployment |
| Analytics Engineer / BI Developer | Contracts, dbt, DAX, dashboards, QA, handoff |

Все роли условные. Их запросы имитируются через training tickets.

## 2. Правила работы

### Один ticket — одна branch

```bash
git switch main
git pull --ff-only
git switch -c feature/<ticket-id>-<short-name>
```

Не смешивайте в одном change set:

- исправление DAX;
- автоматическую Power BI normalization;
- новый dbt mart;
- документацию несвязанного бизнес-правила.

### WIP limit

Одновременно выполняется один основной ticket. Второй ticket допускается только
как небольшая blocker-задача.

### Сначала решение, потом код

```text
Business question
    → metric/rule definition
    → grain and source
    → acceptance criteria
    → implementation
    → independent validation
    → report/UAT
    → PR/release
```

### Evidence обязательно

«У меня работает» не является доказательством. Для каждого ticket сохраняются:

- SQL result;
- dbt test/build output;
- Power BI screenshot или точные значения;
- список проверенных filters;
- business IDs контрольных строк;
- `git diff --cached`;
- limitations и decision log.

## 3. Рабочий ритм

### Каждый рабочий день

1. Проверить ticket и ожидаемое business decision.
2. Выполнить `git status` и убедиться в правильной branch.
3. Проверить доступность PostgreSQL и freshness при необходимости.
4. Проверить grain/source/definition до изменения кода.
5. Реализовать минимальный change.
6. Прогнать подходящие tests.
7. Независимо пересчитать ключевой результат.
8. Обновить документацию.
9. Просмотреть staged diff.
10. Записать короткий worklog.

Шаблон daily update:

```text
Date:
Ticket:
Yesterday:
Today:
Blocker:
Decision needed:
Validation evidence:
Next step:
```

### Недельный ритм

| День | Церемония |
| --- | --- |
| Понедельник | Planning: выбрать 2–4 tickets и определить outcome |
| Вторник | Source/grain investigation и implementation |
| Среда | Metric/data-contract review |
| Четверг | SQL reconciliation, Power BI UAT и PR self-review |
| Пятница | Demo, retrospective и release candidate |

Раз в две недели выполняется sprint review.

## 4. Типы tickets

| Prefix | Тип работы |
| --- | --- |
| `BR` | Business rule |
| `MET` | Metric definition |
| `DATA` | Source/import/contract |
| `AE` | dbt staging/mart/test |
| `BI` | DAX, relationship, page или visual |
| `DQ` | Data-quality rule или remediation |
| `INC` | Incident investigation |
| `OPS` | Pipeline, CI, environment |
| `ADR` | Architecture decision |
| `DOC` | Documentation |
| `UAT` | Business acceptance |
| `REL` | Release/rollback |

Используйте [work_item.md](templates/work_item.md) для каждого нового ticket.

## 5. Definition of Ready

Ticket готов к разработке, когда известны:

- requester;
- business question;
- решение, которое будет принято;
- current и expected behavior;
- grain;
- reporting date;
- population и exclusions;
- currency/unit;
- source of truth;
- acceptance criteria;
- out of scope.

Если определение существенно меняет результат, не угадывайте его — оформите
`Decision needed`.

## 6. Definition of Done

Ticket считается завершённым, если:

- business rule однозначен и имеет status;
- grain и keys зафиксированы;
- source и affected layers перечислены;
- dbt contracts/tests проходят;
- результат независимо пересчитан SQL;
- Power BI проверен без filters и на трёх control slices;
- агрегат раскрывается до business ID;
- DQ exclusion видим и объясним;
- документация обновлена;
- staged diff просмотрен;
- секреты и machine-specific параметры не попали в Git;
- UAT/evidence приложены;
- rollback или безопасный recovery описан.

## 7. Программа: 4 спринта / 8 недель

Первые шесть недель составляют обязательную core-программу. Недели 7–8
добавляют production-like operations и portfolio handoff.

## Sprint 1 — Trust and Billing Foundation

### Неделя 1. Business onboarding и доверие к KPI

Сюжет:

> Head of Finance спрашивает, что означает текущий revenue KPI и почему ему
> можно доверять.

Tickets:

- `BA-101` — утвердить business case, stakeholders и decision map;
- `MET-102` — заполнить definitions для headline KPIs;
- `QA-103` — пройти invoice от CSV до Power BI;
- `INC-104` — оформить Windows → Mac PostgreSQL connectivity incident.

Практика:

1. Прочитать `docs/business_case.md`.
2. Для каждого KPI заполнить [metric_spec.md](templates/metric_spec.md).
3. Проследить три invoices:
   - correct paid non-USD;
   - amount mismatch;
   - missing currency или failed.
4. Сверить SQL и Power BI без filters.

Acceptance:

- `Net Revenue USD` не называется recognized revenue;
- grain/date/population/exclusions понятны;
- три invoice прослежены до raw/source row;
- SQL и Power BI totals совпадают;
- connectivity incident имеет impact/root cause/recovery.

Portfolio evidence:

- architecture map;
- KPI dictionary;
- reconciliation output;
- incident report.

### Неделя 2. Data reliability и controlled defects

Сюжет:

> Finance видит изменение суммы после refresh и просит объяснить, что произошло.

Tickets:

- `DQ-201` — проверить freshness и batch lineage;
- `DQ-202` — расследовать invoice amount mismatch;
- `BI-203` — сделать DQ detail table actionable;
- `QA-204` — доказать raw/staging/mart key parity.

Simulated incidents:

- stale load;
- missing FX coverage;
- mismatch KPI не раскрывается до invoice;
- invoice исключён из certified amount без видимого объяснения.

Acceptance:

- DQ card count = SQL count = detail population;
- каждая проблема имеет business ID;
- указан owner team;
- issue не удаляется из fact;
- impact, root cause, workaround и prevention записаны.

## Sprint 2 — Commercial and Product Analytics

### Неделя 3. Revenue and Plans

Сюжет:

> Finance и Revenue Operations хотят понять plan и billing-frequency mix.

Tickets:

- `BUG-301` — исправить `canceled/cancelled`;
- `MET-302` — развести eligible paid invoice amount, billed amount, cash и
  recognized revenue;
- `MET-303` — исправить определение Active Paid Workspaces;
- `BI-304` — построить страницу `Revenue and Plans`;
- `QA-305` — сверить один month, plan, currency и workspace.

Simulated incident:

> Total совпадает, но после выбора plan Power BI расходится с SQL.

Acceptance:

- SQL и Power BI совпадают до `0.01`;
- no-filter и четыре control slices проверены;
- plan и billing-frequency definitions видимы;
- date relationship соответствует KPI;
- из агрегата можно перейти к invoices.

### Неделя 4. Acquisition and Product Usage

Сюжет:

> Growth хочет понять, какие first-touch sources приводят активные и платящие
> workspace.

Tickets:

- `MET-401` — описать workspace first-touch attribution;
- `BI-402` — построить `Acquisition and Usage`;
- `BI-403` — проверить inactive date relationships;
- `ANL-404` — сравнить acquisition, usage и paid outcome.

Simulated incident:

> Date slicer меняет invoices, но не sessions/events.

Acceptance:

- session visuals используют `Sessions By Session Date`;
- event visuals используют `Events By Event Date`;
- invited user не перезаписывает workspace acquisition;
- три monthly slices сверены SQL;
- correlation usage/billing не выдается за causation;
- используемая дата написана на странице или в tooltip.

## Sprint 3 — Customer Operations and Data Quality

### Неделя 5. Workspace 360

Сюжет:

> Customer Success просит объяснить историю одного workspace.

Tickets:

- `BI-501` — создать `Workspace Drill-Through`;
- `ANL-502` — восстановить customer journey;
- `QA-503` — проверить workspace isolation;
- `UAT-504` — выполнить Customer Success acceptance scenario.

Simulated incident:

> Drill-through показывает invoices другого customer или смешивает current
> snapshot с historical period.

Acceptance:

- все visuals ограничены одним workspace;
- видны users, subscription, plan history, invoices и events;
- current и historical measures разделены;
- один workspace полностью прослежен до raw;
- technical keys скрыты на executive pages, business IDs доступны на details.

### Неделя 6. Operational Data Quality

Сюжет:

> ERP owner требует рабочую очередь records, а не только график количества
> ошибок.

Tickets:

- `AE-601` — создать `mart_data_quality_issues`;
- `DQ-602` — определить issue codes, severity и owner;
- `BI-603` — завершить Data Quality Monitor;
- `INC-604` — пройти defect → handoff → source correction → rerun.

Минимальный grain:

```text
одна строка = одна quality issue одного business record
```

Минимальные поля:

```text
issue_key
issue_code
entity_type
business_record_id
workspace_id
field_name
severity
owner_team
load_batch_id
detected_at
```

Acceptance:

- `issue_key` unique/not null;
- issue ведёт к source row;
- issue counts сверяются с исходными flags;
- executive KPI не скрывает факт exclusion;
- повторный pipeline подтверждает исправление.

Ограничение: при текущем replace-load можно честно построить snapshot текущих
issues. `resolution_status`, `resolved_at` и `ticket_id` потребуют stateful
issue history.

## Sprint 4 — Release Engineering and Portfolio

### Неделя 7. CI и production-like environment

Сюжет:

> Tech Lead требует блокировать плохие изменения до merge в `main`.

Tickets:

- `OPS-701` — GitHub Actions static quality gate;
- `SEC-702` — secret и personal-host checks;
- `OPS-703` — dbt parse/build strategy;
- `CLOUD-704` — опциональный managed PostgreSQL demo environment;
- `ADR-705` — записать deployment/credential decision.

Simulated incident:

> В PBIP diff попал personal hostname или `.env`.

Acceptance:

- unit tests и PBIP validator запускаются на PR;
- secret/personal host check блокирует unsafe change;
- credentials находятся только в secrets/environment;
- deployment и rollback задокументированы;
- managed service называется demo, а не production SLA.

### Неделя 8. UAT, release и презентация

Сюжет:

> Stakeholders принимают первую цельную версию аналитического продукта.

Tickets:

- `UAT-801` — пройти role-based business scenarios;
- `REL-802` — подготовить release checklist и notes;
- `DOC-803` — синхронизировать README, scope и screenshots;
- `DEMO-804` — подготовить 5–7 minute product demonstration.

Контрольная ситуация:

> Stakeholder просит MRR и предлагает считать его суммой invoices текущего
> месяца.

Правильное действие — не писать быструю неправильную DAX-меру. Нужно проверить
business rule и создать отдельную subscription-month model.

Acceptance:

- полный pipeline и reconciliation проходят;
- dashboard pages отвечают на decision;
- DQ KPI раскрывается до record;
- release воспроизводим по runbook;
- implemented и roadmap разделены;
- подготовлена демонстрация одного KPI и одного incident.

## 8. Training Backlog

| ID | Priority | Work item | Current status |
| --- | --- | --- | --- |
| BUG-301 | P0 | Исправить `canceled/cancelled` | Ready |
| MET-302 | P0 | Развести financial metric meanings | Decision required |
| MET-303 | P0 | Определить Active Paid Workspaces | Decision required |
| BI-203 | P1 | Предфильтровать DQ detail tables | Ready |
| BI-304 | P1 | Revenue and Plans page | Ready after metric decisions |
| BI-402 | P1 | Acquisition and Usage page | Ready |
| BI-501 | P1 | Workspace Drill-Through | Ready |
| AE-601 | P1 | `mart_data_quality_issues` snapshot | Ready after schema review |
| FIN-610 | P2 | Invoice currency fallback | Business rule draft |
| FIN-611 | P2 | Authoritative FX date | Business rule draft |
| FIN-612 | P2 | Recognized revenue mart | Approved rule, not implemented |
| FIN-613 | P2 | MRR/ARR mart | Approved rule, not implemented |
| OPS-701 | P2 | CI quality gate | Planned |
| CLOUD-704 | P3 | Managed PostgreSQL demo | Optional |

## 9. Incident Library

Каждый incident расследуется по [incident_report.md](templates/incident_report.md).

| Incident | Симптом | Что тренируется |
| --- | --- | --- |
| DB unavailable | Power BI refresh timeout | Network/Docker/host diagnosis |
| FX coverage drop | USD billed amount уменьшился | Coverage gate и financial caveat |
| Join loss | Row count уменьшился в mart | Key parity и FK integrity |
| Join explosion | Сумма выросла после change | Grain и many-to-many |
| DAX context bug | SQL total совпал, slice нет | Relationships/filter context |
| Stale source | Dashboard обновился не новыми data | Effective-date vs load freshness |
| DQ interaction bug | KPI не раскрывает records | Visual interaction и detail filter |
| Secret leak risk | Host/password появился в diff | Git/CI security control |
| Metric disagreement | Finance и Product считают по-разному | Owner/definition/decision log |

Не изменяйте production-like data специально опасной командой. Инцидент можно
симулировать через отдельную branch, fixture, намеренно failing test или
read-only comparison query.

## 10. UAT Scenarios

### Finance

1. Выбрать один invoice month.
2. Сравнить paid invoices и eligible paid net amount с SQL.
3. Проверить FX coverage.
4. Открыть исключённый invoice.

### Billing Operations

1. Открыть amount mismatch population.
2. Найти invoice ID и source row.
3. Определить owner/action.
4. Подтвердить исправление следующим batch.

### Growth

1. Выбрать acquisition source.
2. Проверить workspace attribution.
3. Сравнить customer/usage/paid outcomes.
4. Зафиксировать caveat о correlation.

### Customer Success

1. Drill through в один workspace.
2. Проверить users/subscription/plan history.
3. Сверить invoices и events.
4. Отличить current state от historical period.

## 11. Evidence Package

Для каждого крупного work item сохраняйте:

```text
Ticket:
Branch / commit:
Business definition:
Affected layers:
Data as of:
dbt result:
SQL reconciliation:
Power BI control values:
Filters tested:
Business IDs traced:
Known caveats:
UAT result:
Reviewer:
Rollback:
```

Для release используйте [release_checklist.md](templates/release_checklist.md).

## 12. Что сохранять для портфолио

- GitHub Issue с business request;
- отдельную branch;
- PR с acceptance criteria;
- metric definition;
- SQL reconciliation;
- dbt lineage/test output;
- screenshot dashboard page;
- before/after исправления;
- incident report;
- release notes;
- короткое demo video.

Честная итоговая формулировка:

> Я разработал production-like end-to-end analytics case на синтетических
> данных и отработал discovery, data contracts, dbt transformation, semantic
> modeling, Power BI development, reconciliation, Data Quality, Git review и
> incident analysis.

Не заявляйте реальный production SLA, enterprise ERP integration или
организационный Power BI deployment, пока они не реализованы.

## 13. С чего начать сегодня

Первый рабочий ticket — `MET-102`.

1. Скопировать `docs/templates/metric_spec.md`.
2. Заполнить его для текущей меры `Net Revenue USD`.
3. Назвать безопасное business meaning:
   `Eligible Paid Invoice Net USD (by issue date)`.
4. Сверить одну строку и total с PostgreSQL.
5. Зафиксировать различие между billed, paid, cash и recognized revenue.
6. Создать отдельную branch и commit только для definition/documentation.

После этого переходить к `BUG-301`, а затем к `MET-303`.
