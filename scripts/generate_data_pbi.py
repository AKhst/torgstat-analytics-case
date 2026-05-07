import pandas as pd
import random
from datetime import date, timedelta
import numpy as np

# 1. Справочники
managers = [
    {'ManagerID': 101, 'Name': 'Иванов Иван', 'Region': 'Москва'},
    {'ManagerID': 102, 'Name': 'Петров Петр', 'Region': 'СПб'},
    {'ManagerID': 103, 'Name': 'Сидорова Анна', 'Region': 'Екатеринбург'},
    {'ManagerID': 104, 'Name': 'Кузнецов Алексей', 'Region': 'Москва'},
    {'ManagerID': 105, 'Name': 'Смирнова Ольга', 'Region': 'Казань'}
]

products = [
    {'ProductID': 1, 'ProductName': 'Laptop Pro 15', 'Category': 'Computers', 'Cost': 800, 'Price': 1200},
    {'ProductID': 2, 'ProductName': 'Laptop Air 13', 'Category': 'Computers', 'Cost': 600, 'Price': 900},
    {'ProductID': 3, 'ProductName': 'Gaming Monitor 27', 'Category': 'Peripherals', 'Cost': 200, 'Price': 350},
    {'ProductID': 4, 'ProductName': 'Wireless Mouse', 'Category': 'Accessories', 'Cost': 15, 'Price': 40},
    {'ProductID': 5, 'ProductName': 'Mech Keyboard', 'Category': 'Accessories', 'Cost': 40, 'Price': 100},
    {'ProductID': 6, 'ProductName': 'Office Chair', 'Category': 'Furniture', 'Cost': 100, 'Price': 250},
]

# 2. Генерация Продаж (Fact_Sales)
start_date = date(2024, 1, 1)
end_date = date(2025, 12, 31)
delta = end_date - start_date

sales_data = []

for i in range(delta.days + 1):
    day = start_date + timedelta(days=i)
    
    # Сезонность: в декабре продаж больше
    if day.month == 12:
        daily_transactions = random.randint(10, 25)
    elif day.weekday() >= 5: # Выходные - спад
        daily_transactions = random.randint(0, 5)
    else:
        daily_transactions = random.randint(5, 15)

    for _ in range(daily_transactions):
        mgr = random.choice(managers)
        prod = random.choice(products)
        
        # Немного рандома в количестве
        qty = np.random.choice([1, 1, 1, 2, 3, 5, 10], p=[0.4, 0.2, 0.1, 0.1, 0.1, 0.05, 0.05])
        
        sales_data.append({
            'Date': day,
            'ManagerID': mgr['ManagerID'],
            'ProductID': prod['ProductID'],
            'Quantity': qty,
            'Amount': qty * prod['Price']  # Выручка
        })

# 3. Генерация Планов (Fact_Targets) - Месячные планы на Менеджера
targets_data = []
dates = pd.date_range(start_date, end_date, freq='MS') # Первое число месяца

for d in dates:
    for mgr in managers:
        # Базовый план + рост каждый год + сезонность
        base_target = 15000 
        if d.year == 2025: base_target *= 1.2 # Рост плана на 20%
        if d.month == 12: base_target *= 1.5 # Декабрь
        
        # Немного вариативности
        target = int(base_target * random.uniform(0.9, 1.1))
        
        targets_data.append({
            'MonthDate': d.date(),
            'ManagerID': mgr['ManagerID'],
            'TargetAmount': target
        })

        # Сохранение
df_sales = pd.DataFrame(sales_data)
df_targets = pd.DataFrame(targets_data)
df_managers = pd.DataFrame(managers)
df_products = pd.DataFrame(products)


# ----------------------
# Save all to CSV 
# ----------------------
out_files = {
    "Fact_Sales.csv": df_sales,
    "Fact_Targets.csv": df_targets,
    "Dim_Managers.csv": df_managers,
    "Dim_Products.csv": df_products,
}

for name, df in out_files.items():
    df.to_csv(f"/Users/admin/torgstat-analytics-case/data_pbi/{name}", index=False)

print("Файлы готовы! Загружай в Power BI.")