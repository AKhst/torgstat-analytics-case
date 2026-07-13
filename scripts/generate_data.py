import os
import pandas as pd
import numpy as np
import random
import datetime
import json

# Фиксируем seed для воспроизводимости датасета
random.seed(42)
np.random.seed(42)

# Определяем пути
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

start_date = datetime.date(2023, 1, 1)
end_date = datetime.date(2024, 5, 31)

workspaces = [f"WS_{i:04d}" for i in range(1, 201)]
plans = [
    {'plan_id': 1, 'plan_name': 'Free', 'billing_period': 'monthly', 'price': 0},
    {'plan_id': 2, 'plan_name': 'Starter', 'billing_period': 'monthly', 'price': 29},
    {'plan_id': 3, 'plan_name': 'Pro', 'billing_period': 'annual', 'price': 299},
    {'plan_id': 4, 'plan_name': 'Enterprise', 'billing_period': 'annual', 'price': 999}
]

countries = ['DE', 'UK', 'FR', 'ES', 'NL', 'IT', 'US', 'EU_UNKNOWN', None]

num_users = 2500
users = []
for i in range(num_users):
    ws = random.choice(workspaces)
    # Создаем намеренно грязные даты для тестирования Data Quality
    if random.random() < 0.1:
        signup_date = "2023/13/45" # Невалидная дата
    else:
        days = random.randint(0, 500)
        signup_date = start_date + datetime.timedelta(days=days)
    
    users.append({
        'user_id': i + 1,
        'workspace_id': ws,
        'signup_date': signup_date,
        'country': random.choice(countries),
        'gdpr_consent': random.choice([True, False]),
        'is_deleted': random.random() < 0.05
    })
df_users = pd.DataFrame(users)

subscriptions = []
invoices = []
currencies = ['EUR', 'GBP', 'USD', None]

for ws in workspaces:
    # Случайный выбор плана
    plan = random.choice(plans)
    start = start_date + datetime.timedelta(days=random.randint(0, 300))
    
    sub_id = random.randint(1000, 9999)
    subscriptions.append({
        'subscription_id': sub_id,
        'workspace_id': ws,
        'plan_id': plan['plan_id'],
        'start_date': start,
        'status': random.choice(['active', 'churned', 'MISSING_STATUS'])
    })
    
    # Генерация счетов (инвойсов)
    for month in range(12):
        if random.random() < 0.05: continue # Пропуск некоторых периодов
        
        inv_id = random.randint(10000, 99999)
        gross = plan['price'] * 1.2
        invoices.append({
            'invoice_id': inv_id,
            'subscription_id': sub_id,
            'workspace_id': ws,
            'plan_id': plan['plan_id'],
            'period_start': start + datetime.timedelta(days=month*30),
            'period_end': start + datetime.timedelta(days=(month+1)*30),
            'currency': random.choice(currencies),
            'net_amount': plan['price'],
            'tax_amount': plan['price'] * 0.2,
            'gross_amount': gross if random.random() > 0.1 else -100, # Отрицательная сумма (грязь)
            'paid': random.random() > 0.05 # 5% ошибок оплат
        })

df_subs = pd.DataFrame(subscriptions)
df_invoices = pd.DataFrame(invoices)

events = []
for _ in range(5000):
    events.append({
        'workspace_id': random.choice(workspaces),
        'event_date': start_date + datetime.timedelta(days=random.randint(0, 500)),
        'event_name': random.choice(['dashboard_viewed', 'export_limit_reached', 'login']),
        'properties': json.dumps({'browser': 'chrome'})
    })
df_events = pd.DataFrame(events)

sessions = []
for i in range(1000):
    sessions.append({
        'session_id': f"sess_{i}",
        'user_id': random.randint(1, num_users),
        'session_date': start_date + datetime.timedelta(days=random.randint(0, 500)),
        'utm_source': random.choice(['capterra', 'g2', 'linkedin_ads']),
        'utm_medium': 'cpc',
        'is_first_session': random.random() < 0.2
    })
df_sessions = pd.DataFrame(sessions)

out_files = {
    "plans.csv": pd.DataFrame(plans),
    "users.csv": df_users,
    "sessions.csv": df_sessions,
    "subscriptions.csv": df_subs,
    "invoices.csv": df_invoices,
    "events.csv": df_events
}

for name, df in out_files.items():
    df.to_csv(os.path.join(DATA_DIR, name), index=False)

summary = {k: len(v) for k, v in out_files.items()}
print("✅ Dataset generated successfully in /data/ :")
for k, v in summary.items():
    print(f"  - {k}: {v} rows")