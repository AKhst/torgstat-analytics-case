# Workflow изменения данных

## Цель

Не допускать ситуации, когда CSV, importer, raw, staging, marts и документация описывают разные версии данных.

## Обязательная последовательность

```text
Business rule
→ Data Contract
→ Generator
→ CSV validation
→ Import contract
→ Raw source declaration
→ Staging model and contract
→ Mart model and metric definition
→ Tests
→ dbt Docs
→ Visualization
```

## Шаги изменения

1. Создать или изменить business rule.
2. Получить для правила статус `APPROVED`.
3. Обновить поля и grain в Data Contract.
4. Изменить генератор.
5. Проверить CSV вручную и автоматическими проверками.
6. Обновить `FILE_SCHEMAS` в importer.
7. Обновить dbt source и source tests.
8. Обновить staging SQL и YAML contract.
9. Обновить затронутые marts и определения показателей.
10. Запустить ограниченный dbt build для изменённой ветки.
11. Запустить полный dbt build.
12. Проверить lineage и описания в dbt Docs.
13. Только после этого менять визуализацию.

## Карточка изменения

```markdown
Change ID: DATA-001
Status: DRAFT | APPROVED | IMPLEMENTED
Reason:
Business rule:
Affected source files:
Affected dbt models:
Affected metrics:
Backward compatibility:
Data Quality impact:
Validation commands:
```

## Правило остановки

Если непонятно, как новое поле влияет на grain, валюту, сумму или историчность, изменение не реализуется до принятия бизнес-решения.
