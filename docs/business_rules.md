# Business Rules

## Статус документа

- Версия: `0.5`
- Статус: `DRAFT`
- Реализация: правила workspace, plans, users, sessions, subscriptions и invoices внедряются; invoice currency rules ожидают отдельного утверждения

## Формат правила

Каждое правило содержит:

- стабильный идентификатор;
- бизнес-смысл;
- grain;
- входные поля;
- алгоритм;
- исключения и fallback;
- проверки качества;
- затронутые модели;
- статус согласования.

## Workspace

### BR-WS-001: Workspace является основной B2B-сущностью

- Статус: `APPROVED`
- Grain: один workspace.
- Правило: пользователи принадлежат workspace; подписка и billing оформляются на workspace.
- Следствие: финансовые показатели должны агрегироваться сначала на уровне workspace, а не пользователя.
- Контроль: каждый `workspace_id` в users, subscriptions, invoices и events должен существовать в `workspaces`.

### BR-WS-002: Workspace имеет основную billing currency

- Статус: `APPROVED`
- Grain: один workspace.
- Поле: `workspaces.billing_currency`.
- Допустимые значения: `EUR`, `GBP`, `USD`.
- Правило версии 1: billing currency обязательна и не изменяется после создания workspace.
- Причина ограничения: это позволяет безопасно восстановить пропущенную валюту invoice без исторической таблицы изменений.
- Будущее расширение: при изменяемой валюте потребуется история с `valid_from` и `valid_to`.

### BR-WS-003: Workspace может существовать без подписки

- Статус: `APPROVED`.
- Правило: workspace может быть создан до покупки тарифа.
- Следствие: отсутствие subscription не является Data Quality ошибкой.
- Аналитический смысл: такие workspace участвуют в анализе conversion в платную подписку.

### BR-WS-004: Workspace создаётся вместе с owner

- Статус: `APPROVED`.
- Правило: у каждого workspace должна существовать хотя бы одна строка user с `user_role = owner`.
- Для active workspace должен существовать ровно один active owner.
- Для inactive workspace историческая запись owner сохраняется, но active users могут отсутствовать.
- Контроль: workspace без user является критической Data Quality ошибкой.

## Invoice Currency

### BR-BILL-001: Определение валюты invoice

- Статус: `DRAFT`.
- Grain: один invoice внутри workspace.
- Входные поля: `invoices.currency`, `workspaces.billing_currency`.
- Алгоритм:
  1. Если `invoices.currency` заполнена, используется она.
  2. Если она отсутствует, используется `workspaces.billing_currency`.
  3. Если обе отсутствуют, результат получает `UNRESOLVED`.
- Выходные поля:
  - `source_currency`;
  - `resolved_currency`;
  - `currency_resolution_method`;
  - `is_currency_resolved`.
- Допустимые методы: `invoice`, `workspace_default`, `unresolved`.
- Контроль: fallback не должен скрывать исходный `NULL`.

### BR-BILL-002: Неразрешённая валюта не скрывается

- Статус: `DRAFT`.
- Правило: invoice с `UNRESOLVED` сохраняется в invoice fact.
- Финансовое правило: такой invoice не включается в конвертированную USD-сумму.
- Data Quality правило: количество и исходная сумма таких invoices показываются отдельно.
- Цель: проблему можно передать владельцу Billing/ERP для расследования.

### BR-BILL-003: Намеренная ошибка валюты в синтетических данных

- Статус: `DRAFT`.
- Правило: около 2% invoices намеренно создаются без `currency`.
- Ожидаемое поведение: большинство записей восстанавливаются через workspace default.
- Назначение: проверить fallback, lineage и Data Quality сценарий.
- Ограничение: ошибка не должна составлять текущие 25%, поскольку это нереалистично для штатного источника.

## Subscriptions and Plans

### BR-PLAN-001: Plan описывает продуктовый уровень

- Статус: `APPROVED`.
- Plans версии 1: `Free`, `Starter`, `Pro`, `Enterprise`.
- Порядок определяется `tier_rank` от 0 до 3.
- Monthly и annual являются billing frequency одного plan, а не отдельными plans.

### BR-PLAN-002: Plan содержит monthly и annual net prices

- Статус: `APPROVED`.
- Monthly price применяется к одному месяцу сервиса.
- Annual price применяется к 12 месяцам сервиса.
- Annual price версии 1 равна десяти monthly prices.
- Налог рассчитывается отдельно и не входит в plan price.

### BR-PLAN-003: Цена интерпретируется в billing currency workspace

- Статус: `APPROVED`.
- Числовые значения plan price одинаковы для EUR, GBP и USD workspace.
- Это упрощение синтетической модели, а не рекомендация для реального международного pricing.
- Региональные price books и отдельные цены по валютам исключены из версии 1.

### BR-PLAN-004: Upgrade и downgrade определяются tier rank

- Статус: `APPROVED`.
- Переход на больший rank является upgrade.
- Переход на меньший rank является downgrade.
- Изменение только billing frequency не считается изменением продуктового уровня.
- В версии 1 billing frequency не меняется в течение активной subscription.

## Users and Sessions

### BR-USER-001: User принадлежит одному workspace

- Статус: `APPROVED`.
- Один workspace может иметь много users.
- Один user версии 1 не может одновременно состоять в нескольких workspaces.
- Billing и subscription metrics не агрегируются на grain user.

### BR-USER-002: Workspace имеет одного owner

- Статус: `APPROVED`.
- Owner создаётся вместе с workspace.
- У active workspace должен существовать ровно один активный user с `user_role = owner`.
- Inactive workspace сохраняет историческую запись owner, но может не иметь active users.
- Остальные роли: `admin`, `member`, `analyst`.

### BR-USER-003: Soft-deleted users сохраняются

- Статус: `APPROVED`.
- Удаление заполняет `deleted_at` и устанавливает `is_active = false`.
- Исторические sessions и events не удаляются.
- Удалённый user не учитывается как active user после `deleted_at`.

### BR-SESSION-001: Session не может начаться до создания user

- Статус: `APPROVED`.
- Правило: `sessions.started_at >= users.created_at`.
- Нарушение является критической temporal consistency ошибкой.

### BR-SESSION-002: У пользователя одна first session

- Статус: `APPROVED`.
- Если у user есть sessions, ровно одна из них имеет `is_first_session = true`.
- Это session с минимальным `started_at`.

### BR-SESSION-003: UTM хранится на first session

- Статус: `APPROVED`.
- UTM описывает first-touch user acquisition.
- Последующие sessions не должны повторять UTM attribution.
- Для invited users UTM может отсутствовать и не считается ошибкой.

### BR-SESSION-004: Workspace acquisition наследуется от owner

- Статус: `APPROVED`.
- First-touch source workspace определяется по первой session пользователя с `user_role = owner`.
- UTM приглашённых пользователей не меняет acquisition source workspace.
- Conversion в paid subscription анализируется на grain workspace.

### BR-SUB-001: Workspace может иметь историю subscriptions

- Статус: `APPROVED`.
- Правило: один workspace может иметь несколько subscriptions за всё время.
- Ограничение версии 1: одновременно может существовать максимум одна активная core-подписка.
- Причина: модель остаётся понятной, но поддерживает отмену и последующее повторное подключение.
- Будущее расширение: несколько одновременных subscriptions для разных продуктов или add-ons.

### BR-SUB-002: Subscription сохраняет ID при смене тарифа

- Статус: `APPROVED`.
- Правило: upgrade или downgrade не создаёт новую subscription.
- История: изменение записывается в `subscription_plan_history`.
- Контроль: plan-периоды одной subscription не пересекаются.
- Причина: subscription описывает договорные отношения, а plan — условия в определённый период.

### BR-SUB-003: Смена тарифа действует со следующего billing period

- Статус: `APPROVED`.
- Правило версии 1: изменение plan не пересчитывает уже начавшийся период.
- Upgrade: новый более дорогой plan начинается со следующей даты billing.
- Downgrade: новый более дешёвый plan начинается со следующей даты billing.
- Исключено из версии 1: proration, credit note и доплата внутри периода.

### BR-SUB-004: Invoice является snapshot условий billing

- Статус: `APPROVED`.
- Grain: один выставленный счёт.
- Правило: одна subscription может иметь много invoices.
- Invoice сохраняет `plan_id`, валюту и суммы, действовавшие при его создании.
- Следствие: последующая смена plan не изменяет исторические invoices.

### BR-SUB-005: Периодичность invoice зависит от plan

- Статус: `APPROVED`.
- Monthly plan: один invoice на billing month.
- Annual plan: один invoice на billing year.
- Free plan: финансовый invoice не создаётся.
- Исключено из версии 1: usage-based billing и дополнительные invoice items.

## Invoice Lifecycle

### BR-INV-001: Invoice является неизменяемым billing snapshot

- Статус: `APPROVED`.
- Grain: один invoice за один billing period.
- Invoice сохраняет workspace, subscription, plan, currency и суммы на дату выставления.
- Последующее изменение workspace или plan не переписывает исторический invoice.

### BR-INV-002: Invoice ID глобально уникален

- Статус: `APPROVED`.
- Правило: `invoice_id` уникален во всём источнике, а не только внутри workspace.
- Следствие: случайные коллизии ID удаляются из генератора.
- `workspace_id` всё равно сохраняется для partitioning, lineage и consistency checks.

### BR-INV-003: Payment status имеет ограниченный lifecycle

- Статус: `APPROVED`.
- Допустимые значения версии 1: `pending`, `paid`, `failed`.
- `paid_at` заполняется только для `paid`.
- `pending` означает, что срок оплаты ещё не завершён.
- `failed` означает неуспешную оплату без моделирования отдельных attempts.
- Retry, partial payment, refund и credit note переносятся в следующую версию.

### BR-INV-004: Финансовые суммы должны быть согласованы

- Статус: `APPROVED`.
- Правило: `gross_amount = net_amount + tax_amount`.
- Допуск округления: абсолютное расхождение не больше `0.01`.
- Отрицательные суммы не используются как способ моделирования refund.
- Нарушение формулы является Data Quality проблемой.
- DWH рассчитывает difference, но не выбирает автоматически, какое исходное поле исправлять.
- Issue code: `INVOICE_AMOUNT_RECONCILIATION_MISMATCH`.
- Для расследования передаются `invoice_id`, workspace, три исходные суммы, difference и load batch.
- Настоящие refunds в будущем должны моделироваться отдельной сущностью или credit note.

### BR-INV-005: Analytics eligibility не удаляет исходный invoice

- Статус: `APPROVED`.
- Invoice с проблемой сохраняется в invoice fact.
- Для основной billing суммы используется только корректный оплаченный invoice с разрешённой валютой.
- Исключённые количество и сумма должны быть доступны в Data Quality анализе.

## Billing and Revenue

### BR-FIN-001: Annual plan использует annual prepaid billing

- Статус: `APPROVED`.
- Commitment period: 12 месяцев.
- Billing frequency: один invoice в начале годового периода.
- Invoice amount: полная годовая стоимость.
- Исключено из версии 1: annual commitment с ежемесячной оплатой.

### BR-FIN-002: Billing, cash и revenue используют разные даты

- Статус: `APPROVED`.
- Billing относится к `invoice.issued_at`.
- Cash collection относится к `invoice.paid_at`.
- Recognized revenue относится к месяцу оказания услуги.
- Overdue и aging рассчитываются относительно `invoice.due_at`.
- Эти показатели не должны подменять друг друга в отчётах.

### BR-FIN-003: Annual revenue признаётся равномерно

- Статус: `APPROVED`.
- Правило версии 1: annual `net_amount` распределяется равномерно на 12 service months.
- Формула: `monthly_recognized_revenue = annual_net_amount / 12`.
- Налог не включается в recognized revenue.

### BR-FIN-004: MRR и ARR рассчитываются из subscription value

- Статус: `APPROVED`.
- Monthly plan: `MRR = monthly net price`.
- Annual plan: `MRR = annual net price / 12`.
- `ARR = MRR * 12`.
- MRR и ARR не рассчитываются как сумма invoices за календарный месяц.

## Предварительные решения для следующего обсуждения

После утверждения workspace необходимо отдельно согласовать:

- дата FX-курса для финансовой конвертации.
