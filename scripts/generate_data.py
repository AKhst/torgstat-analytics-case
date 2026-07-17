import datetime as dt
import json
import random
from pathlib import Path

import pandas as pd
from dateutil.relativedelta import relativedelta


SEED = 42
WORKSPACE_COUNT = 200
USER_COUNT = 2500
EVENT_COUNT = 5000
DATA_START = dt.date(2023, 1, 1)
DATA_END = dt.date(2024, 5, 31)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

PLANS = [
    {
        "plan_id": 1,
        "plan_name": "Free",
        "tier_rank": 0,
        "monthly_price": 0,
        "annual_price": 0,
        "is_active": True,
    },
    {
        "plan_id": 2,
        "plan_name": "Starter",
        "tier_rank": 1,
        "monthly_price": 29,
        "annual_price": 290,
        "is_active": True,
    },
    {
        "plan_id": 3,
        "plan_name": "Pro",
        "tier_rank": 2,
        "monthly_price": 79,
        "annual_price": 790,
        "is_active": True,
    },
    {
        "plan_id": 4,
        "plan_name": "Enterprise",
        "tier_rank": 3,
        "monthly_price": 249,
        "annual_price": 2490,
        "is_active": True,
    },
]

COUNTRY_CURRENCY = {
    "DE": "EUR",
    "FR": "EUR",
    "ES": "EUR",
    "IT": "EUR",
    "NL": "EUR",
    "GB": "GBP",
    "US": "USD",
}


def random_date(randomizer: random.Random, start: dt.date, end: dt.date) -> dt.date:
    return start + dt.timedelta(days=randomizer.randint(0, (end - start).days))


def random_timestamp(
    randomizer: random.Random,
    start: dt.datetime,
    end: dt.datetime,
) -> dt.datetime:
    seconds = int((end - start).total_seconds())
    return start + dt.timedelta(seconds=randomizer.randint(0, max(seconds, 0)))


def generate_workspaces(randomizer: random.Random) -> pd.DataFrame:
    rows = []
    countries = list(COUNTRY_CURRENCY)
    for number in range(1, WORKSPACE_COUNT + 1):
        country_code = randomizer.choice(countries)
        rows.append(
            {
                "workspace_id": f"WS_{number:04d}",
                "workspace_name": f"Workspace {number:04d}",
                "created_at": random_date(
                    randomizer,
                    DATA_START,
                    DATA_START + dt.timedelta(days=240),
                ),
                "country_code": country_code,
                "customer_segment": randomizer.choices(
                    ["smb", "mid_market", "enterprise"],
                    weights=[65, 25, 10],
                    k=1,
                )[0],
                "billing_currency": COUNTRY_CURRENCY[country_code],
                "is_active": randomizer.random() >= 0.08,
            }
        )
    return pd.DataFrame(rows)


def generate_users(
    randomizer: random.Random,
    workspaces: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[int, dt.datetime]]:
    workspace_rows = workspaces.to_dict("records")
    rows = []
    valid_created_at = {}

    for user_id, workspace in enumerate(workspace_rows, start=1):
        created_at = dt.datetime.combine(workspace["created_at"], dt.time(hour=9))
        is_active = bool(workspace["is_active"])
        deleted_at = None if is_active else created_at + dt.timedelta(days=300)
        rows.append(
            {
                "user_id": user_id,
                "workspace_id": workspace["workspace_id"],
                "created_at": created_at,
                "country_code": workspace["country_code"],
                "user_role": "owner",
                "signup_type": "self_service",
                "has_gdpr_consent": randomizer.random() >= 0.05,
                "is_active": is_active,
                "deleted_at": deleted_at,
            }
        )
        valid_created_at[user_id] = created_at

    for user_id in range(WORKSPACE_COUNT + 1, USER_COUNT + 1):
        workspace = randomizer.choice(workspace_rows)
        workspace_created_at = dt.datetime.combine(
            workspace["created_at"],
            dt.time(hour=9),
        )
        created_at = random_timestamp(
            randomizer,
            workspace_created_at,
            dt.datetime.combine(DATA_END, dt.time(hour=18)),
        )
        is_active = bool(workspace["is_active"]) and randomizer.random() >= 0.05
        deleted_at = None
        if not is_active:
            deleted_at = random_timestamp(
                randomizer,
                created_at,
                dt.datetime.combine(DATA_END + dt.timedelta(days=180), dt.time(hour=18)),
            )
        rows.append(
            {
                "user_id": user_id,
                "workspace_id": workspace["workspace_id"],
                "created_at": created_at,
                "country_code": (
                    None
                    if randomizer.random() < 0.02
                    else randomizer.choice(list(COUNTRY_CURRENCY))
                ),
                "user_role": randomizer.choices(
                    ["admin", "member", "analyst"],
                    weights=[15, 65, 20],
                    k=1,
                )[0],
                "signup_type": "invited",
                "has_gdpr_consent": randomizer.random() >= 0.08,
                "is_active": is_active,
                "deleted_at": deleted_at,
            }
        )
        valid_created_at[user_id] = created_at

    invalid_candidates = list(range(WORKSPACE_COUNT + 1, USER_COUNT + 1))
    invalid_count = round(USER_COUNT * 0.01)
    for user_id in randomizer.sample(invalid_candidates, invalid_count):
        rows[user_id - 1]["created_at"] = "2023-13-45 09:00:00"

    return pd.DataFrame(rows), valid_created_at


def generate_sessions(
    randomizer: random.Random,
    users: pd.DataFrame,
    valid_created_at: dict[int, dt.datetime],
) -> pd.DataFrame:
    owner_ids = users.loc[users["user_role"] == "owner", "user_id"].tolist()
    additional_ids = randomizer.sample(
        users.loc[users["user_role"] != "owner", "user_id"].tolist(),
        450,
    )
    selected_user_ids = owner_ids + additional_ids
    user_lookup = users.set_index("user_id").to_dict("index")
    rows = []
    session_number = 1

    for user_id in selected_user_ids:
        user = user_lookup[user_id]
        created_at = valid_created_at[user_id]
        session_count = randomizer.randint(1, 3)
        first_started_at = random_timestamp(
            randomizer,
            created_at,
            dt.datetime.combine(DATA_END + dt.timedelta(days=30), dt.time(hour=23)),
        )
        first_source = randomizer.choice(["capterra", "g2", "linkedin_ads", "organic"])
        first_medium = "organic" if first_source == "organic" else "cpc"
        if user["signup_type"] == "invited" and randomizer.random() < 0.7:
            first_source = None
            first_medium = None
        elif randomizer.random() < 0.01:
            first_source = None

        for occurrence in range(session_count):
            started_at = first_started_at + dt.timedelta(
                days=occurrence * randomizer.randint(1, 30),
                hours=randomizer.randint(0, 12),
            )
            rows.append(
                {
                    "session_id": f"sess_{session_number:06d}",
                    "user_id": user_id,
                    "started_at": started_at,
                    "utm_source": first_source if occurrence == 0 else None,
                    "utm_medium": first_medium if occurrence == 0 else None,
                    "is_first_session": occurrence == 0,
                }
            )
            session_number += 1

    return pd.DataFrame(rows).sort_values("session_id").reset_index(drop=True)


def generate_subscriptions(
    randomizer: random.Random,
    workspaces: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    subscription_id = 1001
    subscribed_workspaces = workspaces.sample(
        n=170,
        random_state=SEED,
    ).sort_values("workspace_id")
    repeat_workspace_ids = set(
        subscribed_workspaces.loc[subscribed_workspaces["is_active"]]
        .sample(n=10, random_state=SEED + 1)["workspace_id"]
        .tolist()
    )

    for workspace in subscribed_workspaces.to_dict("records"):
        started_at = random_date(
            randomizer,
            workspace["created_at"],
            min(workspace["created_at"] + dt.timedelta(days=120), DATA_END),
        )
        if workspace["workspace_id"] in repeat_workspace_ids:
            ended_at = min(started_at + dt.timedelta(days=180), DATA_END - dt.timedelta(days=45))
            rows.append(
                {
                    "subscription_id": subscription_id,
                    "workspace_id": workspace["workspace_id"],
                    "started_at": started_at,
                    "ended_at": ended_at,
                    "status": "cancelled",
                }
            )
            subscription_id += 1
            started_at = ended_at + dt.timedelta(days=30)

        if workspace["is_active"]:
            status = randomizer.choices(
                ["active", "past_due", "trial", "cancelled"],
                weights=[72, 8, 8, 12],
                k=1,
            )[0]
        else:
            status = "cancelled"
        ended_at = None
        if status == "cancelled":
            ended_at = random_date(randomizer, started_at, DATA_END)
        rows.append(
            {
                "subscription_id": subscription_id,
                "workspace_id": workspace["workspace_id"],
                "started_at": started_at,
                "ended_at": ended_at,
                "status": status,
            }
        )
        subscription_id += 1

    return pd.DataFrame(rows)


def add_billing_period(start: dt.date, billing_frequency: str) -> dt.date:
    if billing_frequency == "annual":
        return start + relativedelta(years=1)
    return start + relativedelta(months=1)


def generate_plan_history(
    randomizer: random.Random,
    subscriptions: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    period_id = 1
    plan_lookup = {plan["plan_id"]: plan for plan in PLANS}

    for subscription in subscriptions.to_dict("records"):
        initial_plan_id = randomizer.choices([1, 2, 3, 4], weights=[20, 40, 30, 10], k=1)[0]
        billing_frequency = (
            "monthly"
            if initial_plan_id == 1
            else randomizer.choices(["monthly", "annual"], weights=[70, 30], k=1)[0]
        )
        valid_from = subscription["started_at"]
        subscription_end = subscription["ended_at"] or DATA_END
        billing_step_end = add_billing_period(valid_from, billing_frequency)
        change_date = add_billing_period(billing_step_end, billing_frequency)
        can_change = change_date <= subscription_end and randomizer.random() < 0.35

        if not can_change:
            rows.append(
                {
                    "subscription_plan_period_id": period_id,
                    "subscription_id": subscription["subscription_id"],
                    "plan_id": initial_plan_id,
                    "billing_frequency": billing_frequency,
                    "valid_from": valid_from,
                    "valid_to": subscription["ended_at"],
                    "change_type": "initial",
                }
            )
            period_id += 1
            continue

        current_rank = plan_lookup[initial_plan_id]["tier_rank"]
        available_plan_ids = [
            plan_id
            for plan_id, plan in plan_lookup.items()
            if plan["tier_rank"] != current_rank
        ]
        next_plan_id = randomizer.choice(available_plan_ids)
        next_rank = plan_lookup[next_plan_id]["tier_rank"]
        rows.append(
            {
                "subscription_plan_period_id": period_id,
                "subscription_id": subscription["subscription_id"],
                "plan_id": initial_plan_id,
                "billing_frequency": billing_frequency,
                "valid_from": valid_from,
                "valid_to": change_date - dt.timedelta(days=1),
                "change_type": "initial",
            }
        )
        period_id += 1
        rows.append(
            {
                "subscription_plan_period_id": period_id,
                "subscription_id": subscription["subscription_id"],
                "plan_id": next_plan_id,
                "billing_frequency": billing_frequency,
                "valid_from": change_date,
                "valid_to": subscription["ended_at"],
                "change_type": "upgrade" if next_rank > current_rank else "downgrade",
            }
        )
        period_id += 1

    return pd.DataFrame(rows)


def generate_invoices(
    randomizer: random.Random,
    workspaces: pd.DataFrame,
    subscriptions: pd.DataFrame,
    plan_history: pd.DataFrame,
) -> pd.DataFrame:
    workspace_lookup = workspaces.set_index("workspace_id").to_dict("index")
    subscription_lookup = subscriptions.set_index("subscription_id").to_dict("index")
    plan_lookup = {plan["plan_id"]: plan for plan in PLANS}
    rows = []
    invoice_id = 10001

    for period in plan_history.to_dict("records"):
        subscription = subscription_lookup[period["subscription_id"]]
        workspace = workspace_lookup[subscription["workspace_id"]]
        plan = plan_lookup[period["plan_id"]]
        if plan["tier_rank"] == 0:
            continue

        period_limit = period["valid_to"] or subscription["ended_at"] or DATA_END
        service_start = period["valid_from"]
        while service_start <= min(period_limit, DATA_END):
            next_service_start = add_billing_period(service_start, period["billing_frequency"])
            service_end = next_service_start - dt.timedelta(days=1)
            if service_end > period_limit and period["valid_to"] is not None:
                break
            issued_at = service_start
            due_at = issued_at + dt.timedelta(days=14)
            payment_status = randomizer.choices(
                ["paid", "failed"],
                weights=[97, 3],
                k=1,
            )[0]
            if due_at > DATA_END:
                payment_status = "pending"
            paid_at = None
            if payment_status == "paid":
                paid_at = issued_at + dt.timedelta(days=randomizer.randint(0, 14))

            price_field = (
                "annual_price" if period["billing_frequency"] == "annual" else "monthly_price"
            )
            net_amount = round(float(plan[price_field]), 2)
            tax_amount = round(net_amount * 0.2, 2)
            gross_amount = round(net_amount + tax_amount, 2)
            if randomizer.random() < 0.01:
                gross_amount = round(gross_amount + 5.0, 2)

            rows.append(
                {
                    "invoice_id": invoice_id,
                    "subscription_id": period["subscription_id"],
                    "workspace_id": subscription["workspace_id"],
                    "plan_id": period["plan_id"],
                    "billing_frequency": period["billing_frequency"],
                    "issued_at": issued_at,
                    "due_at": due_at,
                    "period_start": service_start,
                    "period_end": service_end,
                    "currency": (
                        None
                        if randomizer.random() < 0.02
                        else workspace["billing_currency"]
                    ),
                    "net_amount": net_amount,
                    "tax_amount": tax_amount,
                    "gross_amount": gross_amount,
                    "payment_status": payment_status,
                    "paid_at": paid_at,
                }
            )
            invoice_id += 1
            service_start = next_service_start

    return pd.DataFrame(rows)


def generate_events(
    randomizer: random.Random,
    workspaces: pd.DataFrame,
) -> pd.DataFrame:
    workspace_rows = workspaces.to_dict("records")
    rows = []
    for _ in range(EVENT_COUNT):
        workspace = randomizer.choice(workspace_rows)
        rows.append(
            {
                "workspace_id": workspace["workspace_id"],
                "event_date": random_date(randomizer, workspace["created_at"], DATA_END),
                "event_name": randomizer.choice(
                    ["dashboard_viewed", "export_limit_reached", "login"]
                ),
                "properties": json.dumps({"browser": randomizer.choice(["chrome", "safari", "firefox"])}),
            }
        )
    return pd.DataFrame(rows)


def validate_generated_data(
    datasets: dict[str, pd.DataFrame],
    valid_created_at: dict[int, dt.datetime],
) -> None:
    workspaces = datasets["workspaces.csv"]
    users = datasets["users.csv"]
    sessions = datasets["sessions.csv"]
    subscriptions = datasets["subscriptions.csv"]
    plan_history = datasets["subscription_plan_history.csv"]
    invoices = datasets["invoices.csv"]

    if workspaces["workspace_id"].duplicated().any():
        raise ValueError("workspace_id must be globally unique")
    if users["user_id"].duplicated().any():
        raise ValueError("user_id must be globally unique")
    if sessions["session_id"].duplicated().any():
        raise ValueError("session_id must be globally unique")
    if subscriptions["subscription_id"].duplicated().any():
        raise ValueError("subscription_id must be globally unique")
    if plan_history["subscription_plan_period_id"].duplicated().any():
        raise ValueError("subscription_plan_period_id must be globally unique")
    if invoices["invoice_id"].duplicated().any():
        raise ValueError("invoice_id must be globally unique")

    active_workspace_ids = set(workspaces.loc[workspaces["is_active"], "workspace_id"])
    owner_counts = users.loc[users["user_role"] == "owner"].groupby("workspace_id").size()
    active_owners = users.loc[
        (users["user_role"] == "owner") & users["is_active"]
    ].groupby("workspace_id").size()
    if any(owner_counts.get(workspace_id, 0) != 1 for workspace_id in workspaces["workspace_id"]):
        raise ValueError("Every workspace must have exactly one owner record")
    if any(active_owners.get(workspace_id, 0) != 1 for workspace_id in active_workspace_ids):
        raise ValueError("Every active workspace must have exactly one active owner")
    if set(workspaces["workspace_id"]) - set(users["workspace_id"]):
        raise ValueError("Every workspace must have at least one user")

    first_session_counts = sessions.groupby("user_id")["is_first_session"].sum()
    if not (first_session_counts == 1).all():
        raise ValueError("Every user with sessions must have exactly one first session")
    earliest_sessions = sessions.sort_values(
        ["user_id", "started_at", "session_id"]
    ).groupby("user_id", as_index=False).first()
    if not earliest_sessions["is_first_session"].all():
        raise ValueError("The earliest session must be marked as the first session")
    if sessions.loc[~sessions["is_first_session"], ["utm_source", "utm_medium"]].notna().any().any():
        raise ValueError("UTM attribution is only allowed on first sessions")
    if any(
        row.started_at < valid_created_at[row.user_id]
        for row in sessions.itertuples(index=False)
    ):
        raise ValueError("Sessions cannot start before their users are created")

    subscription_lookup = subscriptions.set_index("subscription_id").to_dict("index")
    for workspace_id, workspace_subscriptions in subscriptions.groupby("workspace_id"):
        ordered = workspace_subscriptions.sort_values("started_at").to_dict("records")
        for previous, current in zip(ordered, ordered[1:]):
            if previous["ended_at"] is None or current["started_at"] <= previous["ended_at"]:
                raise ValueError(f"Subscriptions overlap for {workspace_id}")

    for subscription_id, periods in plan_history.groupby("subscription_id"):
        ordered = periods.sort_values("valid_from").to_dict("records")
        for previous, current in zip(ordered, ordered[1:]):
            if previous["valid_to"] is None or current["valid_from"] <= previous["valid_to"]:
                raise ValueError(f"Plan periods overlap for subscription {subscription_id}")

    plan_ranks = {plan["plan_id"]: plan["tier_rank"] for plan in PLANS}
    history_by_subscription = {
        subscription_id: periods.to_dict("records")
        for subscription_id, periods in plan_history.groupby("subscription_id")
    }
    for invoice in invoices.to_dict("records"):
        subscription = subscription_lookup[invoice["subscription_id"]]
        if subscription["workspace_id"] != invoice["workspace_id"]:
            raise ValueError("Invoice workspace must match its subscription")
        matching_periods = [
            period
            for period in history_by_subscription[invoice["subscription_id"]]
            if period["plan_id"] == invoice["plan_id"]
            and period["billing_frequency"] == invoice["billing_frequency"]
            and invoice["period_start"] >= period["valid_from"]
            and (period["valid_to"] is None or invoice["period_start"] <= period["valid_to"])
        ]
        if len(matching_periods) != 1:
            raise ValueError("Invoice must match exactly one subscription plan period")
        if plan_ranks[invoice["plan_id"]] == 0:
            raise ValueError("Free plan periods cannot produce invoices")
        if invoice["period_end"] <= invoice["period_start"]:
            raise ValueError("Invoice billing period must be positive")
        if invoice["due_at"] < invoice["issued_at"]:
            raise ValueError("Invoice due date cannot precede its issue date")
        if (invoice["payment_status"] == "paid") != (invoice["paid_at"] is not None):
            raise ValueError("Invoice paid_at must match payment_status")
        if min(invoice["net_amount"], invoice["tax_amount"], invoice["gross_amount"]) < 0:
            raise ValueError("Invoice amounts cannot be negative")


def main() -> None:
    randomizer = random.Random(SEED)
    workspaces = generate_workspaces(randomizer)
    users, valid_created_at = generate_users(randomizer, workspaces)
    sessions = generate_sessions(randomizer, users, valid_created_at)
    subscriptions = generate_subscriptions(randomizer, workspaces)
    plan_history = generate_plan_history(randomizer, subscriptions)
    invoices = generate_invoices(
        randomizer,
        workspaces,
        subscriptions,
        plan_history,
    )
    events = generate_events(randomizer, workspaces)

    datasets = {
        "workspaces.csv": workspaces,
        "plans.csv": pd.DataFrame(PLANS),
        "users.csv": users,
        "sessions.csv": sessions,
        "subscriptions.csv": subscriptions,
        "subscription_plan_history.csv": plan_history,
        "invoices.csv": invoices,
        "events.csv": events,
    }
    validate_generated_data(datasets, valid_created_at)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for file_name, dataframe in datasets.items():
        dataframe.to_csv(DATA_DIR / file_name, index=False)

    print("Dataset generated successfully:")
    for file_name, dataframe in datasets.items():
        print(f"  - {file_name}: {len(dataframe)} rows")


if __name__ == "__main__":
    main()
