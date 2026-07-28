# Data Contract

## Статус документа

- Версия: `1.1`
- Статус: `APPROVED` для core entities; `DRAFT` для `events v1` и `fx_rates v1`
- Утверждено: `workspaces v1`, `plans v1`, `users v1`, `sessions v1`, `subscriptions v1`, `subscription_plan_history v1`, `invoices v1`
- Текущий предмет согласования: `events v1`, `fx_rates v1`, invoice currency fallback и authoritative FX date
- Реализация: generator, import contract и dbt-слои core entities реализованы; результат конкретного запуска подтверждается validation evidence, а не этим статическим документом

## Текущее состояние проекта

Генератор создаёт отдельный `workspaces.csv` с 200 идентификаторами вида `WS_0001`, после чего использует `workspace_id` в:

- `users.csv`;
- `subscriptions.csv`;
- `invoices.csv`;
- `events.csv`.

CSV-контракт содержит собственные атрибуты компании: основную валюту, страну
регистрации, сегмент и дату создания. `dim_workspaces` уже строится из
`stg_workspaces`; прежняя реконструкция workspace через объединение других
staging-моделей больше не является текущим состоянием.

## Сущность `workspaces`

### Бизнес-смысл

`Workspace` — компания-клиент SaaS-продукта. Пользователи работают внутри workspace, а подписка и billing принадлежат компании, а не отдельному пользователю.

### Grain

Одна строка представляет один workspace в его текущем состоянии.

### Ключ

- Primary key: `workspace_id`.
- Формат синтетических значений: `WS_0001`.
- В версии 1 отдельный хешированный `workspace_key` не обязателен.

### Поля v1

| Поле | Тип | Обязательное | Правило | Статус |
| --- | --- | --- | --- | --- |
| `workspace_id` | string | да | Уникальный идентификатор компании | APPROVED |
| `workspace_name` | string | да | Синтетическое название компании | APPROVED |
| `created_at` | date | да | Дата создания workspace | APPROVED |
| `country_code` | string | да | Страна регистрации компании | APPROVED |
| `customer_segment` | string | да | `smb`, `mid_market` или `enterprise` | APPROVED |
| `billing_currency` | string | да | `EUR`, `GBP` или `USD` | APPROVED |
| `is_active` | boolean | да | Текущее состояние workspace | APPROVED |

### Связи

```text
workspaces.workspace_id 1 ─── * users.workspace_id
workspaces.workspace_id 1 ─── * subscriptions.workspace_id
workspaces.workspace_id 1 ─── * invoices.workspace_id
workspaces.workspace_id 1 ─── * events.workspace_id
```

`invoices.workspace_id` сохраняется, хотя workspace также можно определить через subscription. Это позволяет:

- разделять данные клиентов на уровне источника;
- быстрее расследовать проблемы;
- проверять согласованность invoice и subscription;
- не терять принадлежность invoice при проблеме со связью subscription.

### Отличие страны workspace от страны пользователя

`workspaces.country_code` описывает страну регистрации компании. `users.country` описывает страну пользователя. Эти значения могут отличаться и не должны автоматически заменять друг друга.

## CSV v1

```csv
workspace_id,workspace_name,created_at,country_code,customer_segment,billing_currency,is_active
WS_0001,Acme Analytics,2023-01-15,DE,mid_market,EUR,true
```

## Чек-лист реализации

1. `scripts/generate_data.py` генерирует `workspaces.csv` первым — `IMPLEMENTED`.
2. `scripts/import_to_postgres.py` валидирует и загружает файл — `IMPLEMENTED`.
3. `raw.workspaces` объявлен в dbt sources — `IMPLEMENTED`.
4. `staging.stg_workspaces` создан — `IMPLEMENTED`.
5. `marts.dim_workspaces` строится из `stg_workspaces` — `IMPLEMENTED`.
6. Relationships-тесты для `workspace_id` добавлены — `IMPLEMENTED`.
7. Fallback пустой invoice currency на `workspaces.billing_currency` —
   `DRAFT`; текущая модель сохраняет флаг и исключает такую строку из
   certified USD amount.

## Критерии утверждения `workspaces`

Перед статусом `APPROVED` должны быть приняты решения:

- достаточно ли трёх customer segments;
- может ли billing currency изменяться со временем;
- нужна ли дата деактивации workspace;
- требуется ли историческая запись owner для inactive workspace;
- может ли workspace существовать без подписки;
- нужна ли отдельная от `is_active` lifecycle-модель.

Для первой версии billing currency не изменяется, workspace может существовать без подписки, но не без исторической записи user-owner. Active workspace обязан иметь ровно одного active owner; lifecycle workspace ограничивается полем `is_active`.

Эти решения утверждены для `workspaces v1`. Workspace создаётся вместе с owner; отсутствие хотя бы одной строки user является критической Data Quality ошибкой.

## Связь workspace, subscription, plan и invoice

```text
workspaces 1 ─── * subscriptions 1 ─── * invoices
                       │
                       └── * subscription_plan_history * ─── 1 plans
```

Это означает:

- один workspace может иметь много subscriptions за всю историю;
- в первой версии у workspace может быть максимум одна активная core-подписка одновременно;
- одна subscription получает много invoices;
- subscription может менять plan, не меняя свой `subscription_id`;
- invoice сохраняет plan и цену, действовавшие в момент выставления счёта.

## Реализация subscriptions v1

Генератор поддерживает workspace без subscription, повторное подключение после отмены и смену тарифа внутри стабильного `subscription_id`. История upgrade и downgrade хранится отдельно в `subscription_plan_history.csv`.

Файл `plans.csv` уже существует и содержит `Free`, `Starter`, `Pro` и `Enterprise`.

## Сущность `subscriptions`

### Grain

Одна строка представляет одну стабильную core-подписку workspace.

### Поля v1

| Поле | Тип | Обязательное | Правило | Статус |
| --- | --- | --- | --- | --- |
| `subscription_id` | integer | да | Стабильный ID подписки | APPROVED |
| `workspace_id` | string | да | Владелец подписки | APPROVED |
| `started_at` | date | да | Дата начала подписки | APPROVED |
| `ended_at` | nullable date | нет | Дата окончательного закрытия | APPROVED |
| `status` | string | да | `trial`, `active`, `past_due`, `cancelled` | APPROVED |

Текущий `plan_id` не используется как единственный источник истории, потому что при обновлении строки будет потерян предыдущий тариф.

## Сущность `subscription_plan_history`

### Grain

Одна строка представляет период, в течение которого subscription использовала конкретный plan.

| Поле | Тип | Обязательное | Правило | Статус |
| --- | --- | --- | --- | --- |
| `subscription_plan_period_id` | integer | да | Уникальный ID периода | APPROVED |
| `subscription_id` | integer | да | Ссылка на subscription | APPROVED |
| `plan_id` | integer | да | Тариф периода | APPROVED |
| `billing_frequency` | string | да | `monthly` или `annual` | APPROVED |
| `valid_from` | date | да | Начало действия тарифа | APPROVED |
| `valid_to` | nullable date | нет | Конец действия; `NULL` для текущего | APPROVED |
| `change_type` | string | да | `initial`, `upgrade` или `downgrade` | APPROVED |

Периоды одной subscription не должны пересекаться.

## Связь с invoices

Одна subscription может иметь много invoices. Invoice должен хранить:

- `subscription_id` — к какой подписке относится счёт;
- `workspace_id` — контроль принадлежности компании;
- `plan_id` — snapshot тарифа на дату счёта;
- исходные суммы и валюту на дату выставления.

Для первой версии upgrade или downgrade начинает действовать со следующего billing period. Proration, credit notes и перерасчёт внутри периода пока не моделируются.

## Сущность `invoices`

### Grain

Одна строка представляет один выставленный счёт за один billing period одной subscription.

### Поля v1

| Поле | Тип | Обязательное | Правило | Статус |
| --- | --- | --- | --- | --- |
| `invoice_id` | integer | да | Глобально уникальный ID счёта | APPROVED |
| `subscription_id` | integer | да | Подписка, по которой создан счёт | APPROVED |
| `workspace_id` | string | да | Snapshot владельца счёта | APPROVED |
| `plan_id` | integer | да | Snapshot тарифа на дату выставления | APPROVED |
| `billing_frequency` | string | да | Snapshot частоты billing | APPROVED |
| `issued_at` | date | да | Дата выставления счёта | APPROVED |
| `due_at` | date | да | Срок оплаты | APPROVED |
| `period_start` | date | да | Начало оплачиваемого периода | APPROVED |
| `period_end` | date | да | Конец оплачиваемого периода | APPROVED |
| `currency` | nullable string | нет | Исходная валюта invoice | APPROVED |
| `net_amount` | decimal | да | Сумма без налога | APPROVED |
| `tax_amount` | decimal | да | Налог | APPROVED |
| `gross_amount` | decimal | да | Итоговая сумма | APPROVED |
| `payment_status` | string | да | `pending`, `paid` или `failed` | APPROVED |
| `paid_at` | nullable date | нет | Дата успешной оплаты | APPROVED |

### Ограничения версии 1

- `invoice_id` генерируется последовательно и не сталкивается между workspace.
- Monthly plan создаёт invoice раз в месяц.
- Annual plan создаёт invoice раз в год.
- Free plan не создаёт финансовый invoice.
- Upgrade и downgrade применяются только со следующего billing period.
- Одна строка invoice хранит неизменяемый snapshot plan, currency и amount.
- Payment retries, partial payments, refunds и credit notes пока не выделяются в отдельные сущности.

### Намеренные Data Quality сценарии

- около 2% invoices имеют пустую исходную валюту;
- около 1% invoices намеренно получают нарушение `net + tax = gross` для проверки reconciliation-контроля;
- около 3% invoices получают `payment_status = failed`;
- ошибки создаются явно и документированно, а не возникают из случайных коллизий ID.

Нарушение `net + tax = gross` не считается допустимым бизнес-событием. Оно имитирует дефект Billing/ERP, ошибку интеграции или повреждение выгрузки. DWH не определяет автоматически, какое из трёх полей неверно, и не пересчитывает источник без утверждённого правила.

Для расследования рассчитываются:

- `amount_reconciliation_difference = gross_amount - net_amount - tax_amount`;
- `has_amount_reconciliation_mismatch`;
- Data Quality issue code `INVOICE_AMOUNT_RECONCILIATION_MISMATCH`.

Расхождение до `0.01` включительно допускается как техническая погрешность округления. Более крупное расхождение исключает invoice из основного billing KPI и передаётся владельцу Billing вместе с `invoice_id`, исходными суммами, workspace и load batch.

### Правило аналитической пригодности

Invoice может участвовать в основном billing KPI, если:

- `payment_status = paid`;
- исходная invoice currency заполнена и для неё найден требуемый FX rate;
- суммы не отрицательные;
- выполняется `net_amount + tax_amount = gross_amount`;
- billing period корректен.

Непригодный invoice сохраняется в факте и отображается в Data Quality показателях.
Fallback на `workspaces.billing_currency` остаётся целевым правилом со статусом
`DRAFT` и в текущую analytics eligibility не входит.

## Разделение финансовых временных линий

Для одного annual prepaid invoice различаются четыре независимых показателя:

| Показатель | Дата | Смысл |
| --- | --- | --- |
| Billed amount | `issued_at` | Когда выставлен invoice |
| Cash collected | `paid_at` | Когда получена оплата |
| Recognized revenue | service month | За какой месяц оказана услуга |
| MRR / ARR | active subscription month | Нормализованная recurring value |

Пример: annual net price `1 200 EUR` за 12 месяцев создаёт один invoice на `1 200 EUR`, но recognized revenue и MRR составляют `100 EUR` в месяц.

Налог не включается в recognized revenue и MRR. Для этих показателей используется `net_amount`.

## Назначение invoice dates

- `issued_at` — когда юридически или операционно создан invoice; используется для billed amount и количества выставленных счетов.
- `due_at` — крайний срок оплаты; используется для overdue и aging.
- `paid_at` — дата получения оплаты; используется для cash collection и payment delay.
- `period_start` / `period_end` — период оказания услуги; используется для recognized revenue и subscription analytics.

Эти даты могут отличаться. Например, invoice может быть выставлен 20 декабря, относиться к сервисному периоду с 1 января и быть оплачен 5 января.

## Сущность `plans`

### Бизнес-смысл

`Plan` — уровень продукта и доступного функционала. Monthly или annual — это способ оплаты одного plan, а не отдельный продукт.

### Grain

Одна строка представляет один продуктовый plan.

### Поля v1

| Поле | Тип | Обязательное | Правило | Статус |
| --- | --- | --- | --- | --- |
| `plan_id` | integer | да | Уникальный ID plan | APPROVED |
| `plan_name` | string | да | `Free`, `Starter`, `Pro`, `Enterprise` | APPROVED |
| `tier_rank` | integer | да | Порядок plan для upgrade/downgrade | APPROVED |
| `monthly_price` | decimal | да | Net price за один месяц | APPROVED |
| `annual_price` | decimal | да | Net price за один год | APPROVED |
| `is_active` | boolean | да | Доступен ли plan для новых продаж | APPROVED |

### Цены версии 1

| Plan | Rank | Monthly | Annual | Annual discount |
| --- | ---: | ---: | ---: | ---: |
| Free | 0 | 0 | 0 | 0% |
| Starter | 1 | 29 | 290 | два месяца бесплатно |
| Pro | 2 | 79 | 790 | два месяца бесплатно |
| Enterprise | 3 | 249 | 2,490 | два месяца бесплатно |

Числовая цена интерпретируется в `workspaces.billing_currency`. Это сознательное упрощение версии 1: отдельные региональные price books и разные цены по валютам пока не моделируются.

### Использование в subscription

`subscription_plan_history` хранит одновременно:

- `plan_id` — уровень продукта;
- `billing_frequency` — monthly или annual;
- период действия комбинации.

Upgrade означает переход на plan с большим `tier_rank`. Downgrade означает переход на меньший `tier_rank`. Изменение только billing frequency не является upgrade или downgrade и в версии 1 не моделируется.

### Использование в invoice

Invoice сохраняет snapshot:

- `plan_id`;
- `billing_frequency`;
- рассчитанные суммы.

Исторический invoice не пересчитывается при последующем изменении plan price.

## Сущность `users`

### Бизнес-смысл

`User` — учётная запись человека, работающего внутри workspace. Финансовые отношения принадлежат workspace, а не user.

### Grain

Одна строка представляет одного пользователя в его текущем состоянии.

### Поля v1

| Поле | Тип | Обязательное | Правило | Статус |
| --- | --- | --- | --- | --- |
| `user_id` | integer | да | Глобально уникальный ID пользователя | APPROVED |
| `workspace_id` | string | да | Workspace пользователя | APPROVED |
| `created_at` | timestamp | да | Время создания пользователя | APPROVED |
| `country_code` | nullable string | нет | Страна пользователя | APPROVED |
| `user_role` | string | да | `owner`, `admin`, `member`, `analyst` | APPROVED |
| `signup_type` | string | да | `self_service` или `invited` | APPROVED |
| `has_gdpr_consent` | boolean | да | Consent-флаг пользователя | APPROVED |
| `is_active` | boolean | да | Может ли пользователь работать в продукте | APPROVED |
| `deleted_at` | nullable timestamp | нет | Дата soft deletion | APPROVED |

### Правила версии 1

- Один user принадлежит ровно одному workspace.
- Один workspace может иметь много users.
- У каждого workspace должна существовать одна историческая запись `owner`.
- У каждого active workspace должен быть ровно один active `owner`.
- `owner` создаётся вместе с workspace и имеет `signup_type = self_service`.
- Остальные пользователи могут быть приглашены.
- Удалённый user сохраняется для исторической аналитики.
- Страна пользователя может отличаться от страны регистрации workspace.

### Намеренные Data Quality сценарии

- около 2% users имеют пустой `country_code`;
- около 1% users получают некорректный `created_at` в raw-выгрузке;
- такие записи не удаляются, а получают quality flags в staging.

## Сущность `sessions`

### Бизнес-смысл

`Session` — один факт входа и использования продукта конкретным пользователем.

### Grain

Одна строка представляет одну пользовательскую сессию.

### Поля v1

| Поле | Тип | Обязательное | Правило | Статус |
| --- | --- | --- | --- | --- |
| `session_id` | string | да | Глобально уникальный ID session | APPROVED |
| `user_id` | integer | да | Пользователь session | APPROVED |
| `started_at` | timestamp | да | Начало session | APPROVED |
| `utm_source` | nullable string | нет | First-touch acquisition source | APPROVED |
| `utm_medium` | nullable string | нет | First-touch acquisition medium | APPROVED |
| `is_first_session` | boolean | да | Первая ли это session пользователя | APPROVED |

### Правила версии 1

- Один user может иметь ноль или много sessions.
- `started_at` не может быть раньше `users.created_at`.
- Для пользователя с sessions должна существовать ровно одна `is_first_session = true`.
- UTM-поля заполняются только для first session и не копируются в каждую следующую session.
- Приглашённый пользователь может иметь пустые UTM-поля.
- Sessions используются для product usage и user acquisition, но финансовая conversion анализируется на grain workspace.
- Acquisition source workspace определяется по first session его owner.

### Намеренные Data Quality сценарии

- около 1% first sessions имеют потерянный `utm_source`;
- нарушение `session.started_at >= user.created_at` не генерируется намеренно и считается критической ошибкой pipeline/source.

## Сущность `events` — DRAFT

### Бизнес-смысл и grain

`Event` — один факт продуктового действия внутри workspace. Одна строка
представляет одно occurrence; источник версии 1 не предоставляет устойчивый
`event_id`.

### Поля v1

| Поле | Тип | Обязательное | Правило | Статус |
| --- | --- | --- | --- | --- |
| `workspace_id` | string | да | Workspace, в котором произошло действие | DRAFT |
| `event_date` | date | да | Календарная дата события | DRAFT |
| `event_name` | string | да | `dashboard_viewed`, `export_limit_reached` или `login` | DRAFT |
| `properties` | JSON string | нет | Дополнительные свойства события | DRAFT |

Staging создаёт технический surrogate key из payload и номера occurrence.
Одинаковый payload в один день не следует автоматически считать бизнес-дублем:
без source `event_id` это известное ограничение контракта. До утверждения
event identity продуктовые показатели считаются directional usage signals, а
не auditable transaction counts.

## Сущность `fx_rates` — DRAFT

### Бизнес-смысл и grain

`FX rate` — курс одной валютной пары на одну календарную дату. Уникальный grain:
`rate_date + base_currency + quote_currency`.

### Поля v1

| Поле | Тип | Обязательное | Правило | Статус |
| --- | --- | --- | --- | --- |
| `rate_date` | date | да | Дата применимости курса | DRAFT |
| `base_currency` | string | да | Исходная валюта суммы | DRAFT |
| `quote_currency` | string | да | Reporting currency; текущая модель использует USD | DRAFT |
| `rate` | decimal | да | Положительный multiplicative conversion rate | DRAFT |

Для production-like контракта ещё нужно утвердить provider, timezone/cut-off,
holiday/weekend fallback, revision policy и authoritative invoice date
(`issued_at`, `paid_at` или service date). До этого USD conversion полезна для
учебной аналитики, но не должна описываться как бухгалтерски сертифицированная.
