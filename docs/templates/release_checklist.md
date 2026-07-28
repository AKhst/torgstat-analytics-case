# Release checklist: [VERSION / TICKET]

## Scope and approval

- [ ] Ticket содержит business question и decision
- [ ] Metric/contract changes имеют owner и `APPROVED` status
- [ ] Scope соответствует diff
- [ ] Known limitations записаны
- [ ] UAT owner определён

## Data and dbt

- [ ] Source freshness/availability проверена
- [ ] Row counts и ключи сверены
- [ ] `dbt build` прошёл
- [ ] Singular и generic tests прошли
- [ ] Critical totals независимо пересчитаны SQL
- [ ] DQ populations объяснены

## Power BI

- [ ] PBIP validator и regression tests прошли
- [ ] DAX reconciled с mart SQL
- [ ] Date relationships работают ожидаемо
- [ ] Slicers и visual interactions проверены
- [ ] Drill-through раскрывает business ID
- [ ] Empty/error states просмотрены
- [ ] Credentials, LAN IP и local cache не попали в diff

## Git and documentation

- [ ] Power BI Desktop закрыт перед pull/merge
- [ ] `git status` просмотрен
- [ ] `git diff` и `git diff --cached` просмотрены
- [ ] Только намеренные PBIR/TMDL normalization changes включены
- [ ] Business case, rules, contract и runbook обновлены при необходимости
- [ ] Secret scan не обнаружил чувствительных данных

## Release and rollback

- Release owner:
- Release timestamp:
- Commit/tag:
- Refresh evidence:
- UAT result:
- Rollback procedure:
- Final decision: `GO | GO WITH WARNING | NO-GO`
