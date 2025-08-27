import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Параметры
num_customers = 500
regions = ["Москва", "Санкт-Петербург", "Казань", "Новосибирск", "Екатеринбург", "Нижний Новгород"]

# Генерация клиентов
customers = []
for i in range(1, num_customers + 1):
    signup_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 150))
    region = random.choice(regions)
    customers.append([i, signup_date.strftime("%Y-%m-%d"), region])

df_customers = pd.DataFrame(customers, columns=["customer_id", "signup_date", "region"])
df_customers.to_csv("customers.csv", index=False)

# Генерация заказов
orders = []
order_id = 1001
for c_id, signup_date, _ in customers:
    num_orders = np.random.choice([0,1,2,3,4,5], p=[0.1,0.3,0.3,0.15,0.1,0.05])
    for _ in range(num_orders):
        order_date = datetime.strptime(signup_date, "%Y-%m-%d") + timedelta(days=random.randint(1,120))
        total_amount = random.randint(500, 5000)
        orders.append([order_id, c_id, order_date.strftime("%Y-%m-%d"), total_amount])
        order_id += 1

df_orders = pd.DataFrame(orders, columns=["order_id", "customer_id", "order_date", "total_amount"])
df_orders.to_csv("orders.csv", index=False)

print("Генерация CSV завершена!")

