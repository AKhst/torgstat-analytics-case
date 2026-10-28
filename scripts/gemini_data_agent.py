"""Интерактивный Chat-to-Data агент Gemini для аналитики продаж.

Пример запуска:
    export GEMINI_API_KEY="..."
    python scripts/gemini_data_agent.py "Какая выручка по плану Pro за 2023-06?"

По умолчанию агент читает только проверенные витрины PostgreSQL под read-only
ролью. Режим CSV доступен исключительно для локальной отладки.
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Any

import httpx
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text

DEFAULT_MODEL_NAME = "gemini-3.8-flash"
MAX_TOOL_ROUNDS = 5
SYSTEM_INSTRUCTION = """
Ты строгий и профессиональный аналитик данных для проекта Torgstat.

Правила работы:
1. Отвечай только на основании данных, возвращенных доступными инструментами.
2. Не придумывай значения, строки, валюты, периоды или бизнес-выводы.
3. Если для ответа нужны продажи или счета, обязательно используй get_sales_metrics.
4. Явно называй период, категорию, валюту и показатель, о котором говоришь.
5. total_net_amount_usd означает eligible net invoice amount в USD,
    рассчитанный витриной; не называй его cash collection или accounting revenue.
6. Если данных недостаточно или запрос неоднозначен, честно сообщи об этом
   и попроси уточнить запрос.
7. Не показывай внутренний JSON вызова инструмента; дай короткий понятный
   аналитический ответ и укажи ограничения результата.
""".strip()

_sales_data: pd.DataFrame | None = None
_data_source = "неизвестный источник"


def load_sales_data(data_dir: Path) -> pd.DataFrame:
    """Загрузить инвойсы и справочник планов в единый аналитический DataFrame."""
    invoices_path = data_dir / "invoices.csv"
    plans_path = data_dir / "plans.csv"
    invoices = pd.read_csv(invoices_path, parse_dates=["issued_at"])
    plans = pd.read_csv(plans_path)

    sales = invoices.merge(
        plans[["plan_id", "plan_name"]],
        on="plan_id",
        how="left",
        validate="many_to_one",
    )
    sales["plan_name"] = sales["plan_name"].fillna("Unknown")
    sales["analytics_net_amount_usd"] = sales["net_amount"]
    return sales


def build_mart_database_url() -> URL:
    """Создать URL к marts с учётной записью только для чтения."""
    required_environment = (
        "READONLY_USER",
        "READONLY_PASSWORD",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DB",
    )
    missing = [name for name in required_environment if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            "Для источника marts не заданы переменные PostgreSQL: "
            + ", ".join(missing)
        )

    return URL.create(
        "postgresql+psycopg2",
        username=os.environ["READONLY_USER"],
        password=os.environ["READONLY_PASSWORD"],
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ["POSTGRES_PORT"]),
        database=os.environ["POSTGRES_DB"],
    )


def load_mart_data() -> pd.DataFrame:
    """Загрузить проверенные eligible invoice-данные из PostgreSQL marts."""
    schema = os.getenv("MARTS_SCHEMA", "marts")
    if not schema.replace("_", "").isalnum():
        raise ValueError("MARTS_SCHEMA содержит недопустимое имя схемы")

    query = text(f"""
        select
            invoices.issued_at,
            invoices.source_currency_code as currency,
            invoices.payment_status,
            invoices.analytics_net_amount_usd,
            plans.plan_name
        from {schema}.fct_invoices_converted as invoices
        inner join {schema}.dim_plans as plans
            on plans.plan_key = invoices.plan_key
        where invoices.is_analytics_eligible
          and invoices.analytics_net_amount_usd is not null
    """)
    engine = create_engine(build_mart_database_url())
    with engine.connect() as connection:
        sales = pd.read_sql(query, connection, parse_dates=["issued_at"])
    engine.dispose()
    return sales


def configure_data(data: pd.DataFrame, source_description: str) -> None:
    """Установить источник данных, который будет использоваться инструментом."""
    global _data_source, _sales_data
    _sales_data = data
    _data_source = source_description


def _period_bounds(period: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Преобразовать YYYY или YYYY-MM или YYYY-MM-DD в границы периода."""
    normalized_period = period.strip()
    if not re.fullmatch(r"\d{4}(?:-\d{2})?(?:-\d{2})?", normalized_period):
        raise ValueError("period должен иметь формат YYYY, YYYY-MM или YYYY-MM-DD")

    if re.fullmatch(r"\d{4}", normalized_period):
        parsed_period = pd.Period(normalized_period, freq="Y")
    elif re.fullmatch(r"\d{4}-\d{2}", normalized_period):
        parsed_period = pd.Period(normalized_period, freq="M")
    else:
        parsed_period = pd.Period(normalized_period, freq="D")
    return parsed_period.start_time, parsed_period.end_time


def get_sales_metrics(category: str, period: str) -> dict[str, Any]:
    """Вернуть агрегаты продаж по плану и периоду.

    В этом демо category соответствует plan_name (например, ``Pro``),
    а period фильтрует дату выпуска инвойса issued_at. В продакшене внутри
    этой функции можно заменить DataFrame-фильтр на параметризованный SQL.
    """
    if _sales_data is None:
        raise RuntimeError("Источник данных не настроен")

    start_date, end_date = _period_bounds(period)
    filtered = _sales_data.loc[
        _sales_data["issued_at"].between(start_date, end_date)
    ].copy()

    normalized_category = category.strip().casefold()
    if normalized_category not in {"", "all", "все"}:
        filtered = filtered.loc[
            filtered["plan_name"].astype(str).str.casefold() == normalized_category
        ]

    currency_totals = (
        filtered.groupby("currency", dropna=False)["analytics_net_amount_usd"]
        .sum()
        .round(2)
        .to_dict()
    )

    return {
        "category": category,
        "period": period,
        "period_field": "issued_at",
        "invoice_count": int(len(filtered)),
        "paid_invoice_count": int((filtered["payment_status"] == "paid").sum()),
        "net_amount_usd_by_source_currency": {
            str(currency): float(amount)
            for currency, amount in currency_totals.items()
        },
        "total_net_amount_usd": float(
            filtered["analytics_net_amount_usd"].sum().round(2)
        ),
        "data_source": _data_source,
    }


def create_client() -> Any:
    """Создать Gemini-клиент, не позволяя ключу попадать в код или Git."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Не задан GEMINI_API_KEY. Установите переменную окружения перед запуском."
        )
    from google import genai

    return genai.Client(api_key=api_key)


def answer_question(client: Any, question: str) -> str:
    """Выполнить ручной цикл Gemini: вопрос -> tool -> tool result -> ответ."""
    from google.genai import types

    contents: list[Any] = [question]
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        tools=[get_sales_metrics],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        temperature=0.1,
    )

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", DEFAULT_MODEL_NAME),
            contents=contents,
            config=config,
        )
        function_calls = response.function_calls or []
        if not function_calls:
            return response.text or "Модель не вернула текстовый ответ."

        contents.append(response.candidates[0].content)
        for function_call in function_calls:
            if function_call.name != "get_sales_metrics":
                raise RuntimeError(f"Неизвестный инструмент: {function_call.name}")

            arguments = dict(function_call.args or {})
            try:
                tool_result = get_sales_metrics(**arguments)
            except (TypeError, ValueError, RuntimeError) as error:
                tool_result = {"error": str(error)}

            contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_function_response(
                            name=function_call.name,
                            response={"result": tool_result},
                        )
                    ],
                )
            )

    raise RuntimeError("Превышено максимальное число раундов вызова инструментов")


def parse_args() -> argparse.Namespace:
    """Разобрать аргументы командной строки."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", nargs="?", help="Вопрос на естественном языке")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data",
        help="Каталог с invoices.csv и plans.csv",
    )
    parser.add_argument(
        "--source",
        choices=("mart", "csv"),
        default="mart",
        help="Источник данных: проверенная PostgreSQL-витрина или CSV для отладки",
    )
    return parser.parse_args()


def main() -> None:
    """Запустить одноразовый запрос или небольшой интерактивный режим."""
    load_dotenv()
    from google.genai import errors

    args = parse_args()
    if args.source == "csv":
        configure_data(
            load_sales_data(args.data_dir),
            "debug CSV invoices.csv joined with plans.csv; no FX conversion",
        )
    else:
        configure_data(
            load_mart_data(),
            "PostgreSQL marts.fct_invoices_converted joined with marts.dim_plans",
        )
    client = create_client()

    if args.question:
        try:
            print(answer_question(client, args.question))
        except httpx.ProxyError as error:
            raise RuntimeError(
                "Gemini API недоступен через текущий proxy. "
                "Разрешите generativelanguage.googleapis.com в proxy ruleset "
                "или запустите на сети без блокировки Google API. "
                f"Детали: {error}"
            ) from error
        except errors.ClientError as error:
            if error.code == 429:
                raise RuntimeError(
                    "Gemini API отклонил запрос: исчерпана квота проекта (429). "
                    "Проверьте лимиты и billing в Google AI Studio. "
                    "Смена модели может не помочь, если лимит общий для проекта."
                ) from error
            raise
        return

    print("Введите вопрос о продажах. Для выхода введите exit или quit.")
    while True:
        question = input("> ").strip()
        if question.casefold() in {"exit", "quit", "выход"}:
            break
        if question:
            try:
                print(answer_question(client, question))
            except httpx.ProxyError as error:
                print(
                    "Ошибка сети: текущий proxy блокирует Gemini API. "
                    "Разрешите generativelanguage.googleapis.com в proxy ruleset. "
                    f"Детали: {error}"
                )
            except errors.ClientError as error:
                if error.code == 429:
                    print(
                        "Ошибка Gemini: исчерпана квота проекта (429). "
                        "Проверьте лимиты и billing в Google AI Studio."
                    )
                else:
                    raise


if __name__ == "__main__":
    main()
