# Generate synthetic SaaS dataset with realistic data quality issues for ETL processing
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

random.seed(42)
np.random.seed(42)

# ----------------------
# Parameters
# ----------------------
N_USERS = 2000
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2024, 5, 31)
REGIONS = ["Москва", "Санкт-Петербург", "Казань", "Новосибирск", "Екатеринбург", "Нижний Новгород"]
SOURCES = ["google", "yandex", "direct", "referral", "social", "email"]
MEDIUMS = {
    "google": "cpc",
    "yandex": "cpc",
    "direct": "direct",
    "referral": "referral",
    "social": "social",
    "email": "email"
}

PLANS = [
    {"plan_id": 1, "plan_name": "Basic", "period": "monthly", "price": 499.0},
    {"plan_id": 2, "plan_name": "Pro", "period": "monthly", "price": 999.0},
    {"plan_id": 3, "plan_name": "Business", "period": "monthly", "price": 1999.0},
]

# Conversion probabilities by source
CONV_PROB = {
    "google": 0.42,
    "yandex": 0.38,
    "direct": 0.25,
    "referral": 0.35,
    "social": 0.20,
    "email": 0.30,
}

# Monthly churn (hazard) probabilities by plan (approx)
CHURN_PROB = {
    1: 0.30,  # Basic
    2: 0.22,  # Pro
    3: 0.15   # Business
}

# Upper bound on renewals to simulate
MAX_RENEWALS = 5  # in addition to initial payment (so up to 6 invoices total)

# ----------------------
# Helpers
# ----------------------
def rand_date(start: datetime, end: datetime) -> datetime:
    delta = (end - start).days
    return start + timedelta(days=int(np.random.randint(0, delta + 1)))

def month_add(d: datetime, months: int) -> datetime:
    # simple month add: add months assuming 30 days blocks to keep it simple
    return d + timedelta(days=30 * months)

def pick_region() -> str:
    # mildly skewed distribution toward Moscow & SPB
    weights = [0.30, 0.20, 0.15, 0.13, 0.12, 0.10]
    return random.choices(REGIONS, weights=weights, k=1)[0]

def pick_source() -> str:
    weights = [0.28, 0.22, 0.18, 0.12, 0.10, 0.10]  # bias to paid search
    return random.choices(SOURCES, weights=weights, k=1)[0]

def pick_campaign(source: str) -> str:
    if source in ("google", "yandex"):
        return random.choice(["brand", "competitors", "generic", "retargeting"])
    if source == "social":
        return random.choice(["stories", "feed", "influencers"])
    if source == "email":
        return random.choice(["onboarding", "reactivation", "promo"])
    if source == "referral":
        return random.choice(["partner_a", "partner_b", "friend_ref"])
    return "(none)"

# ----------------------
# Generate users with data quality issues
# ----------------------
users = []
sessions = []

for user_id in range(1, N_USERS + 1):
    signup = rand_date(START_DATE, END_DATE)
    region = pick_region()
    source = pick_source()
    medium = MEDIUMS[source]
    campaign = pick_campaign(source)

    # Introduce data quality issues for 5% of users
    if random.random() < 0.05:
        # Missing region
        region = None
    elif random.random() < 0.03:
        # Invalid region
        region = "Unknown_City_123"
    
    # Invalid date format for 2% of users
    signup_date_str = signup.date().isoformat()
    if random.random() < 0.02:
        signup_date_str = signup.strftime("%d/%m/%Y")  # European format
    
    users.append(
        dict(
            user_id=user_id,
            signup_date=signup_date_str,
            region=region
        )
    )

    # first session at signup
    session_id = f"sess_{user_id}_1"
    session_date_str = signup.date().isoformat()
    
    # Session date issues for 3% of sessions
    if random.random() < 0.03:
        session_date_str = "2024-13-45"  # Invalid date
    
    sessions.append(
        dict(
            session_id=session_id,
            user_id=user_id,
            session_date=session_date_str,
            utm_source=source,
            utm_medium=medium,
            utm_campaign=campaign,
            is_first_session=True
        )
    )

    # extra sessions: Poisson-ish
    extra_n = np.random.poisson(2)  # average 2 extra sessions
    for k in range(extra_n):
        d = signup + timedelta(days=int(np.random.randint(1, 90)))
        if d > END_DATE + timedelta(days=120):  # bound
            d = END_DATE + timedelta(days=120)
        
        session_date_extra = d.date().isoformat()
        # More date issues for extra sessions
        if random.random() < 0.04:
            session_date_extra = d.strftime("%m-%d-%Y")  # US format
        
        # Missing UTM parameters for some sessions
        utm_source_extra = source
        utm_medium_extra = medium
        utm_campaign_extra = campaign
        
        if random.random() < 0.08:
            utm_source_extra = None
        if random.random() < 0.06:
            utm_medium_extra = ""
        
        sessions.append(
            dict(
                session_id=f"sess_{user_id}_{k+2}",
                user_id=user_id,
                session_date=session_date_extra,
                utm_source=utm_source_extra,
                utm_medium=utm_medium_extra,
                utm_campaign=utm_campaign_extra,
                is_first_session=False
            )
        )

df_users = pd.DataFrame(users)
df_sessions = pd.DataFrame(sessions)

# ----------------------
# Generate plans (БЕЗ ДУБЛИКАТОВ!)
# ----------------------
df_plans = pd.DataFrame(PLANS)

# ----------------------
# Subscriptions & invoices with data issues
# ----------------------
subs = []
invoices = []

sub_id_seq = 1001
invoice_id_seq = 50001

for _, u in df_users.iterrows():
    uid = int(u.user_id)
    # Handle invalid date formats
    try:
        signup_date = datetime.fromisoformat(u.signup_date)
    except:
        # Try different date format parsing
        try:
            signup_date = datetime.strptime(u.signup_date, "%d/%m/%Y")
        except:
            signup_date = datetime.strptime(u.signup_date, "%m-%d-%Y") if u.signup_date else START_DATE
    
    # derive source from first session
    user_sessions = df_sessions[df_sessions.user_id == uid]
    if not user_sessions.empty:
        srow = user_sessions.sort_values("session_date").iloc[0]
        source = srow.utm_source
        # Handle None source
        if source is None:
            source = "direct"
    else:
        source = "direct"
    
    # Используем уникальные plan_ids без дубликатов
    plan = random.choices([1, 2, 3], weights=[0.5, 0.35, 0.15], k=1)[0]

    # Безопасное получение вероятности конверсии
    conversion_prob = CONV_PROB.get(source, 0.25)

    # initial conversion
    if random.random() < conversion_prob:
        start_offset = int(np.random.randint(0, 14))  # convert within 0-14 days
        start_date = signup_date + timedelta(days=start_offset)
        
        # Subscription status issues
        status = "active"
        if random.random() < 0.04:
            status = None  # Missing status
        elif random.random() < 0.03:
            status = "UNKNOWN_STATUS"  # Invalid status
        
        subs.append(
            dict(
                subscription_id=sub_id_seq,
                user_id=uid,
                plan_id=plan,
                start_date=start_date.date().isoformat(),
                status=status
            )
        )
        
        # initial invoice with amount issues
        price = float(df_plans.loc[df_plans.plan_id == plan, "price"].iloc[0])
        
        # Negative or zero amounts for some invoices
        if random.random() < 0.02:
            amount = -price  # Negative amount
        elif random.random() < 0.01:
            amount = 0  # Zero amount
        else:
            amount = price
        
        # Invalid date formats for invoices
        period_start_str = start_date.date().isoformat()
        period_end_str = (month_add(start_date, 1)).date().isoformat()
        invoice_date_str = start_date.date().isoformat()
        
        if random.random() < 0.03:
            period_start_str = start_date.strftime("%d/%m/%Y")
        if random.random() < 0.03:
            period_end_str = "invalid_date"
        
        invoices.append(
            dict(
                invoice_id=invoice_id_seq,
                subscription_id=sub_id_seq,
                user_id=uid,
                period_start=period_start_str,
                period_end=period_end_str,
                invoice_date=invoice_date_str,
                amount=amount,
                paid=True,
                is_initial=True
            )
        )
        invoice_id_seq += 1

        # simulate renewals month-by-month with churn probability
        current_date = start_date
        churned = False
        for m in range(1, MAX_RENEWALS + 1):
            if churned:
                break
            # churn check before creating next invoice
            if random.random() < CHURN_PROB[plan]:
                churned = True
                break
            
            # next renewal with potential data issues
            period_start = month_add(start_date, m)
            period_end = month_add(start_date, m+1)
            invoice_date = period_start
            
            # More amount issues for renewals
            renewal_amount = price
            if random.random() < 0.05:
                renewal_amount = price * 1.1  # Price change
            if random.random() < 0.02:
                renewal_amount = "invalid_amount"  # String amount
            
            # Date format issues
            period_start_str = period_start.date().isoformat()
            period_end_str = period_end.date().isoformat()
            invoice_date_str = invoice_date.date().isoformat()
            
            if random.random() < 0.04:
                period_start_str = period_start.strftime("%Y-%m-%d %H:%M:%S")  # Timestamp
            
            invoices.append(
                dict(
                    invoice_id=invoice_id_seq,
                    subscription_id=sub_id_seq,
                    user_id=uid,
                    period_start=period_start_str,
                    period_end=period_end_str,
                    invoice_date=invoice_date_str,
                    amount=renewal_amount,
                    paid=random.random() > 0.05,  # 5% unpaid invoices
                    is_initial=False
                )
            )
            invoice_id_seq += 1
        sub_id_seq += 1

df_subs = pd.DataFrame(subs)
df_invoices = pd.DataFrame(invoices)

# Add some duplicate subscriptions
if not df_subs.empty:
    duplicate_subs = df_subs.sample(n=min(10, len(df_subs)//10))
    df_subs = pd.concat([df_subs, duplicate_subs], ignore_index=True)

# update subscription status for churned ones
if not df_subs.empty:
    try:
        last_invoice_date = df_invoices.groupby("subscription_id")["invoice_date"].max().reset_index()
        last_invoice_date["invoice_date"] = pd.to_datetime(last_invoice_date["invoice_date"], errors='coerce')
        # choose a "now" as END_DATE + 60 days
        NOW = END_DATE + timedelta(days=60)
        last_invoice_date["days_since_last"] = (NOW - last_invoice_date["invoice_date"]).dt.days
        churned_subs = set(last_invoice_date.loc[last_invoice_date["days_since_last"] > 45, "subscription_id"])
        df_subs["status"] = df_subs["subscription_id"].apply(lambda x: "churned" if x in churned_subs else "active")
    except:
        # If date parsing fails, keep original status
        pass

# ----------------------
# Events with data issues
# ----------------------
events = []
EVENT_NAMES = ["app_open", "feature_a", "feature_b"]

def generate_user_events(uid, signup_date):
    base_days = 120
    start = signup_date
    for day in range(base_days):
        d = start + timedelta(days=day)
        
        # Event date issues
        event_date_str = d.date().isoformat()
        if random.random() < 0.04:
            event_date_str = d.strftime("%d-%m-%Y")
        if random.random() < 0.01:
            event_date_str = "future_date_3000"  # Far future date
        
        p_open = max(0.35 * np.exp(-day/25), 0.01)
        if random.random() < p_open:
            # app_open with some missing user_ids
            user_id_val = uid
            if random.random() < 0.02:
                user_id_val = None  # Missing user_id
            
            events.append(
                dict(
                    user_id=user_id_val,
                    event_date=event_date_str,
                    event_name="app_open"
                )
            )
            
            if random.random() < 0.5:
                # Invalid event names
                event_name = random.choice(["feature_a", "feature_b"])
                if random.random() < 0.03:
                    event_name = "unknown_feature_xyz"
                
                events.append(
                    dict(
                        user_id=user_id_val,
                        event_date=event_date_str,
                        event_name=event_name
                    )
                )

# limit event generation to a sample
sample_users = set(np.random.choice(df_users.user_id, size=min(1200, len(df_users)), replace=False))
for _, u in df_users.iterrows():
    uid = int(u.user_id)
    if uid in sample_users:
        try:
            signup_date = datetime.fromisoformat(u.signup_date)
        except:
            try:
                signup_date = datetime.strptime(u.signup_date, "%d/%m/%Y")
            except:
                signup_date = START_DATE
        generate_user_events(uid, signup_date)

df_events = pd.DataFrame(events)

# Add some duplicate events
if not df_events.empty:
    duplicate_events = df_events.sample(n=min(50, len(df_events)//20))
    df_events = pd.concat([df_events, duplicate_events], ignore_index=True)

# ----------------------
# Save all to CSV
# ----------------------
out_files = {
    "plans.csv": df_plans,
    "users.csv": df_users,
    "sessions.csv": df_sessions,
    "subscriptions.csv": df_subs,
    "invoices.csv": df_invoices,
    "events.csv": df_events
}

for name, df in out_files.items():
    df.to_csv(f"/Users/admin/torgstat-analytics-case/data/{name}", index=False)

# Quick summary with data quality issues report
summary = {
    "users": len(df_users),
    "sessions": len(df_sessions),
    "subscriptions": len(df_subs),
    "invoices": len(df_invoices),
    "events": len(df_events),
    "data_quality_issues": {
        "missing_regions": df_users['region'].isna().sum(),
        "invalid_dates": sum(1 for d in df_users['signup_date'] if not isinstance(d, str) or len(d) != 10),
        "missing_utm": df_sessions['utm_source'].isna().sum() + df_sessions['utm_medium'].isna().sum(),
        "negative_amounts": sum(1 for amt in df_invoices['amount'] if isinstance(amt, (int, float)) and amt < 0),
        "duplicate_subs": len(df_subs) - len(df_subs.drop_duplicates(subset='subscription_id')),
        "missing_user_ids": df_events['user_id'].isna().sum()
    }
}

print("Data generation complete with intentional data quality issues:")
print(summary)