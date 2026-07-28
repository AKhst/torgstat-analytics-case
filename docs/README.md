# Проектирование данных

Эта папка используется для согласования данных и бизнес-правил до изменения генератора, dbt-моделей и отчётов.

## Документы

- [business_case.md](business_case.md) — каноническая легенда, бизнес-ценность,
  stakeholders, KPI framework и честные границы проекта.
- [training_program.md](training_program.md) — восьминедельная симуляция
  ежедневной работы Analytics Engineer / BI Developer.
- [data_contract.md](data_contract.md) — grain, ключи, поля и связи исходных сущностей.
- [business_rules.md](business_rules.md) — правила, по которым данные создаются и преобразуются.
- [change_workflow.md](change_workflow.md) — порядок безопасного изменения структуры данных.
- [daily_runbook.md](daily_runbook.md) — запуск, подключение, Git и типовая
  диагностика Mac + Windows VM.
- [validation_runbook.md](validation_runbook.md) — ручная и автоматическая
  проверка от raw data до Power BI.

Рабочие заготовки находятся в [`templates/`](templates/): work item, metric
specification, incident report и release checklist.

## Статусы решений

- `DRAFT` — предложение для обсуждения.
- `APPROVED` — правило согласовано и может быть реализовано.
- `IMPLEMENTED` — правило реализовано и проверено.
- `DEPRECATED` — правило больше не используется.

Изменения, которые меняют бизнес-смысл или контракт, не должны начинаться, пока
затронутые правила и поля не получили статус `APPROVED`. Исследовательский
spike допустим, но его результат не должен попадать в certified reporting.

## Порядок согласования сущностей

1. `workspaces`
2. `plans`
3. `users`
4. `subscriptions`
5. `invoices`
6. `sessions`
7. `events`
8. `fx_rates`

Core contracts до `sessions` включительно описаны и реализованы. `events` и
`fx_rates`, invoice currency fallback, authoritative FX date и as-of paid
customer definition остаются предметом следующего согласования.
