# Generate synthetic SaaS dataset with realistic data quality issues and complex MRR logic
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

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
    "google": 0.42, "yandex": 0.38, "direct": 0.25, 
    "referral": 0.35, "social": 0.20, "email": 0.30
}

# Monthly churn (hazard) probabilities by plan
CHURN_PROB = {
    1: 0.30,  # Basic
    2: 0.22,  # Pro
    3: 0.15   # Business
}

MAX_RENEWALS = 5  # Max renewals to simulate

# ----------------------
# Helpers
# ----------------------
def rand_date(start: datetime, end: datetime) -> datetime:
    delta = (end - start).days
    return start + timedelta(days=int(np.random.randint(0, delta + 1)))

def month_add(d: datetime, months: int) -> datetime:
    return d + timedelta(days=30 * months)

def pick_region() -> str:
    weights = [0.30, 0.20, 0.15, 0.13, 0.12, 0.10]
    return random.choices(REGIONS, weights=weights, k=1)[0]

def pick_source() -> str:
    weights = [0.28, 0.22, 0.18, 0.12, 0.10, 0.10]
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

def get_plan_price(plan_id: int) -> float:
    for p in PLANS:
        if p["plan_id"] == plan_id:
            return float(p["price"])
    return 0.0

# ----------------------
# Generate Users & Sessions
# ----------------------
users = []
sessions = []

for user_id in range(1, N_USERS + 1):
    signup = rand_date(START_DATE, END_DATE)
    region = pick_region()
    source = pick_source()
    medium = MEDIUMS[source]
    campaign = pick_campaign(source)

    # Introduce data quality issues for region
    if random.random() < 0.05:
        region = None
    elif random.random() < 0.03:
        region = "Unknown_City_123"
    
    # Introduce data quality issues for signup_date
    signup_date_str = signup.date().isoformat()
    if random.random() < 0.02:
        signup_date_str = signup.strftime("%d/%m/%Y")
    
    users.append({
        "user_id": user_id,
        "signup_date": signup_date_str,
        "region": region
    })

    # First session at signup
    session_id = f"sess_{user_id}_1"
    session_date_str = signup.date().isoformat()
    
    if random.random() < 0.03:
        session_date_str = "2024-13-45"  # Invalid date
    
    sessions.append({
        "session_id": session_id,
        "user_id": user_id,
        "session_date": session_date_str,
        "utm_source": source,
        "utm_medium": medium,
        "utm_campaign": campaign,
        "is_first_session": True
    })

    # Extra sessions
    extra_n = np.random.poisson(2)
    for k in range(extra_n):
        d = signup + timedelta(days=int(np.random.randint(1, 90)))
        if d > END_DATE + timedelta(days=120):
            d = END_DATE + timedelta(days=120)
        
        session_date_extra = d.date().isoformat()
        if random.random() < 0.04:
            session_date_extra = d.strftime("%m-%d-%Y")
        
        utm_source_extra = source
        utm_medium_extra = medium
        
        if random.random() < 0.08: utm_source_extra = None
        if random.random() < 0.06: utm_medium_extra = ""
        
        sessions.append({
            "session_id": f"sess_{user_id}_{k+2}",
            "user_id": user_id,
            "session_date": session_date_extra,
            "utm_source": utm_source_extra,
            "utm_medium": utm_medium_extra,
            "utm_campaign": campaign,
            "is_first_session": False
        })

df_users = pd.DataFrame(users)
df_sessions = pd.DataFrame(sessions)
df_plans = pd.DataFrame(PLANS)

# ----------------------
# Subscriptions & Invoices (With Advanced MRR Logic)
# ----------------------
subs = []
invoices = []

sub_id_seq = 1001
invoice_id_seq = 50001

for _, u in df_users.iterrows():
    uid = int(u.user_id)
    
    # Safe date parsing
    try:
        signup_date = datetime.fromisoformat(u.signup_date)
    except:
        try: signup_date = datetime.strptime(u.signup_date, "%d/%m/%Y")
        except: signup_date = datetime.strptime(u.signup_date, "%m-%d-%Y") if u.signup_date else START_DATE
    
    # Derive source for conversion probability
    user_sessions = df_sessions[df_sessions.user_id == uid]
    source = "direct"
    if not user_sessions.empty:
        srow = user_sessions.sort_values("session_date").iloc[0]
        if srow.utm_source:
            source = srow.utm_source
            
    start_plan = random.choices([1, 2, 3], weights=[0.5, 0.35, 0.15], k=1)[0]
    conversion_prob = CONV_PROB.get(source, 0.25)

    # --- Initial Conversion ---
    if random.random() < conversion_prob:
        start_offset = int(np.random.randint(0, 14))
        start_date = signup_date + timedelta(days=start_offset)
        
        status = "active"
        if random.random() < 0.04: status = None
        elif random.random() < 0.03: status = "UNKNOWN_STATUS"
        
        subs.append({
            "subscription_id": sub_id_seq,
            "user_id": uid,
            "plan_id": start_plan,
            "start_date": start_date.date().isoformat(),
            "status": status
        })
        
        # --- Initial Invoice ---
        current_plan = start_plan
        price = get_plan_price(current_plan)
        
        # 20% chance for a 50% discount on the first month
        discount_pct = 0.5 if random.random() < 0.20 else 0.0
        amount = price * (1 - discount_pct)
        
        # Data Quality Issues
        if random.random() < 0.02: amount = -price
        elif random.random() < 0.01: amount = 0
        
        period_start_str = start_date.date().isoformat()
        period_end_str = (month_add(start_date, 1)).date().isoformat()
        
        if random.random() < 0.03: period_start_str = start_date.strftime("%d/%m/%Y")
        if random.random() < 0.03: period_end_str = "invalid_date"
        
        invoices.append({
            "invoice_id": invoice_id_seq,
            "subscription_id": sub_id_seq,
            "user_id": uid,
            "plan_id": current_plan,
            "period_start": period_start_str,
            "period_end": period_end_str,
            "invoice_date": start_date.date().isoformat(),
            "amount": amount,
            "discount_pct": discount_pct,
            "paid": True,
            "is_initial": True
        })
        invoice_id_seq += 1

        # --- Renewals ---
        churned = False
        for m in range(1, MAX_RENEWALS + 1):
            if churned: break
            
            # Check Churn
            if random.random() < CHURN_PROB[current_plan]:
                churned = True
                break
            
            # Upgrade / Downgrade Logic
            if current_plan == 1 and random.random() < 0.15: 
                current_plan = 2 # Upgrade Basic -> Pro
            elif current_plan == 2 and random.random() < 0.10: 
                current_plan = 3 # Upgrade Pro -> Business
            elif current_plan == 2 and random.random() < 0.05: 
                current_plan = 1 # Downgrade Pro -> Basic
            
            price = get_plan_price(current_plan)
            period_start = month_add(start_date, m)
            period_end = month_add(start_date, m+1)
            
            # Amount and Date Quality Issues
            renewal_amount = price
            if random.random() < 0.02: renewal_amount = "invalid_amount"
            
            period_start_str = period_start.date().isoformat()
            if random.random() < 0.04: period_start_str = period_start.strftime("%Y-%m-%d %H:%M:%S")
            
            # Failed Payment Logic
            is_paid = random.random() > 0.08 # 8% chance of failure
            
            invoices.append({
                "invoice_id": invoice_id_seq,
                "subscription_id": sub_id_seq,
                "user_id": uid,
                "plan_id": current_plan,
                "period_start": period_start_str,
                "period_end": period_end.date().isoformat(),
                "invoice_date": period_start.date().isoformat(),
                "amount": renewal_amount,
                "discount_pct": 0.0,
                "paid": is_paid,
                "is_initial": False
            })
            invoice_id_seq += 1
            
            # If payment failed, create a successful retry invoice 3 days later
            if not is_paid:
                retry_date = period_start + timedelta(days=3)
                invoices.append({
                    "invoice_id": invoice_id_seq,
                    "subscription_id": sub_id_seq,
                    "user_id": uid,
                    "plan_id": current_plan,
                    "period_start": period_start_str,
                    "period_end": period_end.date().isoformat(),
                    "invoice_date": retry_date.date().isoformat(),
                    "amount": renewal_amount,
                    "discount_pct": 0.0,
                    "paid": True,
                    "is_initial": False
                })
                invoice_id_seq += 1
                
        sub_id_seq += 1

df_subs = pd.DataFrame(subs)
df_invoices = pd.DataFrame(invoices)

# Add duplicate subscriptions
if not df_subs.empty:
    duplicate_subs = df_subs.sample(n=min(10, len(df_subs)//10))
    df_subs = pd.concat([df_subs, duplicate_subs], ignore_index=True)

# Update subscription status for churned users
if not df_subs.empty:
    try:
        last_invoice_date = df_invoices.groupby("subscription_id")["invoice_date"].max().reset_index()
        last_invoice_date["invoice_date"] = pd.to_datetime(last_invoice_date["invoice_date"], errors='coerce')
        NOW = END_DATE + timedelta(days=60)
        last_invoice_date["days_since_last"] = (NOW - last_invoice_date["invoice_date"]).dt.days
        churned_subs = set(last_invoice_date.loc[last_invoice_date["days_since_last"] > 45, "subscription_id"])
        df_subs["status"] = df_subs["subscription_id"].apply(lambda x: "churned" if x in churned_subs else "active")
    except:
        pass

# ----------------------
# Events
# ----------------------
events = []

def generate_user_events(uid: int, signup_date: datetime):
    base_days = 120
    start = signup_date
    for day in range(base_days):
        d = start + timedelta(days=day)
        
        event_date_str = d.date().isoformat()
        if random.random() < 0.04: event_date_str = d.strftime("%d-%m-%Y")
        if random.random() < 0.01: event_date_str = "future_date_3000"
        
        p_open = max(0.35 * np.exp(-day/25), 0.01)
        if random.random() < p_open:
            user_id_val = uid
            if random.random() < 0.02: user_id_val = None
            
            events.append({
                "user_id": user_id_val,
                "event_date": event_date_str,
                "event_name": "app_open"
            })
            
            if random.random() < 0.5:
                event_name = random.choice(["feature_a", "feature_b"])
                if random.random() < 0.03: event_name = "unknown_feature_xyz"
                
                events.append({
                    "user_id": user_id_val,
                    "event_date": event_date_str,
                    "event_name": event_name
                })

# Sample users for events to save processing time
sample_users = set(np.random.choice(df_users.user_id, size=min(1200, len(df_users)), replace=False))
for _, u in df_users.iterrows():
    uid = int(u.user_id)
    if uid in sample_users:
        try: signup_date = datetime.fromisoformat(u.signup_date)
        except:
            try: signup_date = datetime.strptime(u.signup_date, "%d/%m/%Y")
            except: signup_date = START_DATE
        generate_user_events(uid, signup_date)

df_events = pd.DataFrame(events)

if not df_events.empty:
    duplicate_events = df_events.sample(n=min(50, len(df_events)//20))
    df_events = pd.concat([df_events, duplicate_events], ignore_index=True)

# ----------------------
# Save Data
# ----------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

out_files = {
    "plans.csv": df_plans,
    "users.csv": df_users,
    "sessions.csv": df_sessions,
    "subscriptions.csv": df_subs,
    "invoices.csv": df_invoices,
    "events.csv": df_events
}

for name, df in out_files.items():
    df.to_csv(os.path.join(DATA_DIR, name), index=False)

summary = {
    "users": len(df_users),
    "sessions": len(df_sessions),
    "subscriptions": len(df_subs),
    "invoices": len(df_invoices),
    "events": len(df_events)
}
print("✅ Полная генерация данных успешно завершена:")
print(summary)