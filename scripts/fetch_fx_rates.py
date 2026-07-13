from pathlib import Path

import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_PATH = DATA_DIR / "fx_rates.csv"

INVOICES_PATH = DATA_DIR / "invoices.csv"


def get_rate_dates() -> list[str]:
    invoices = pd.read_csv(INVOICES_PATH)
    dates = set()
    for column in ["period_start", "period_end"]:
        for value in invoices[column].dropna().tolist():
            if isinstance(value, str) and value:
                dates.add(value)
    return sorted(dates)


def fetch_rates_for_date(rate_date: str, currencies: list[str]) -> list[dict[str, object]]:
    target_currencies = [currency for currency in currencies if currency != "USD"]
    if not target_currencies:
        return []

    url = f"https://api.frankfurter.app/{rate_date}?from=USD&to={','.join(target_currencies)}"
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    payload = response.json()

    if "rates" not in payload:
        raise ValueError(f"Unexpected payload from FX API for {rate_date}")

    rows: list[dict[str, object]] = [
        {
            "rate_date": rate_date,
            "base_currency": "USD",
            "quote_currency": "USD",
            "rate": 1.0,
        }
    ]

    for currency, rate in payload["rates"].items():
        usd_rate = 1.0 / float(rate)
        rows.append(
            {
                "rate_date": rate_date,
                "base_currency": currency,
                "quote_currency": "USD",
                "rate": round(usd_rate, 6),
            }
        )

    return rows


def fetch_rates() -> pd.DataFrame:
    invoices = pd.read_csv(INVOICES_PATH)
    currencies = sorted({currency for currency in invoices["currency"].dropna().astype(str).tolist() if currency})
    currencies = [currency.upper() for currency in currencies if currency.upper() != ""]
    currencies = sorted(set(currencies) | {"USD"})

    rows: list[dict[str, object]] = []
    for rate_date in get_rate_dates():
        rows.extend(fetch_rates_for_date(rate_date, currencies))

    return pd.DataFrame(rows)


def main() -> None:
    df = fetch_rates()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved FX rates to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
