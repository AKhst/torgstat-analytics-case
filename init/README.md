# PostgreSQL Setup для проекта Analytics

Эта директория содержит конфигурацию и скрипты для развёртывания PostgreSQL с готовой схемой `analytics` и пользователями для работы с данными.

## 📂 Структура
- `init/` — содержит SQL-скрипты инициализации базы:
  - `init.sql` — создаёт схему `analytics` и пользователей.

## 🗄️ Структура базы данных

- **Схема**: `analytics`
  - Все таблицы аналитики и данные приложения находятся в этой схеме.
  - Схема создаётся с правами для `torgadmin`.

### Пользователи и права
| Пользователь | Роль | Права |
|--------------|------|-------|
| `torgadmin`  | суперпользователь базы | Инициализация схем, управление БД и пользователями |
| `appuser`    | приложение | `CONNECT` к `torgdb`, полный доступ (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) к таблицам в схеме `analytics` |
| `readonly`   | аналитик / BI | `CONNECT` к `torgdb`, только чтение (`SELECT`) таблиц в схеме `analytics` |

- **Примечание**: права по умолчанию на новые таблицы схемы `analytics` наследуются автоматически для `appuser` и `readonly` (`ALTER DEFAULT PRIVILEGES`).

## ⚙️ Конфигурация Docker
Используется `docker-compose.yml`:

```yaml
services:
  postgres:
    image: postgres:15
    container_name: torgstat_postgres
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "${POSTGRES_PORT}:5432"
    volumes:
      - ./postgres_data:/var/lib/postgresql/data
      - ./init:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
