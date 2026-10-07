import numpy as np
import pandas as pd
import math

np.random.seed(42)

MONTHS = list(range(1, 13))
DATES = [f"2025-{m:02d}-01" for m in MONTHS]
OUT_DIR = r"Budget vs Actual"



"""
Set drivers
"""

budget_revenue_qty = [840, 1100, 1120, 1200, 1260, 1300, 1340, 840, 1420, 1400, 1500, 800]
budget_revenue_price = 5000  # EUR / unit, constant all year
new_revenue_price = 5200  # EUR / unit, from July

budget_rm_per_unit = 2  # ton / unit,   Standard quantity per Unit
new_rm_per_unit = 2.1  # ton / unit,   New quantity per Unit only in Dec


budget_rm_price = 1300  # EUR / ton
new_rm_price = 1600  # EUR / ton, 

budget_standard_time = 10   # hour / unit,   Standard hours per unit
new_standard_time = 10.3  # hour / unit,   New hours per unit only in Nov

budget_dl_reg_rate = 50  # EUR / hour
budget_dl_ot_rate = 60  # EUR / hour (1.2x regular rate)
new_dl_reg_rate = 55   # EUR / hour   
new_dl_ot_rate = 66   # EUR / hour

workers = 85 
regular_hours = round(workers * 35 * 4.33, 0)

truck = 10    # ton / truck

budget_freight_price = 1500  # EUR / truck
new_freight_price = 2000   # EUR / truck

emergency_repair = 150000   # Jan: unplanned breakdown
reduced_repair = 20000  # Aug: repair has already incurred in Jan

shortfall_units = 400    # Jan: machine breakdown 
add_units = 200    # Mar : 1 new order



"""
Build budget
"""

budget_rm_maint = [54000, 54000, 54000, 54000, 54000, 54000, 54000,
                    108000, 54000, 54000, 54000, 54000]    # Aug: planned major repair & maintenance


budget_rm_qty = [round(budget_revenue_qty[i] * budget_rm_per_unit,2) for i in range(12)]

budget_dl_reg_hours = [regular_hours] * 12

budget_dl_ot_hours = [0] * 12

for i in range(12):
    total_hour = budget_revenue_qty[i] * budget_standard_time
    budget_dl_ot_hours[i] = round(max(total_hour - regular_hours,0),2)

budget_freight_qty = [] 

for i in range(12):
    freight_q = math.ceil(budget_rm_qty[i] / truck) 
    budget_freight_qty.append(freight_q)


"""
Actual revenue
Normal months: +/-3% noise. 
"""

actual_revenue_price = [budget_revenue_price] * 6 + [new_revenue_price] * 6
actual_revenue_qty = [0] * 12  

for i, m in enumerate(MONTHS):
    noise = np.random.uniform(-0.03, 0.03)
    if m  == 1:   
        actual_revenue_qty[0] =  round(budget_revenue_qty[0] * (1 + noise) - shortfall_units)
    elif m == 3:
        actual_revenue_qty[2] = round(budget_revenue_qty[2] * (1 + noise) + add_units)
    else:
        actual_revenue_qty[i] = round(budget_revenue_qty[i] * (1 + noise))


actual_revenue_amount = [actual_revenue_qty[i] * actual_revenue_price[i] for i in range(12)]


"""
Actual raw materials 
"""

actual_rm_qty = [0] * 12
actual_rm_per_unit = [budget_rm_per_unit] * 11 + [new_rm_per_unit]
actual_rm_price = [budget_rm_price] * 10 + [new_rm_price] * 2  

for i in range(12):
        qty = actual_revenue_qty[i] * actual_rm_per_unit[i]
        actual_rm_qty[i] = round(qty,2) 

actual_rm_amount = [actual_rm_qty[i] * actual_rm_price[i] for i in range(12)]

"""
Actual direct labor
"""

actual_dl_reg_hours = budget_dl_reg_hours.copy()
actual_dl_reg_rate = [budget_dl_reg_rate] * 4 + [new_dl_reg_rate] * 8   
actual_dl_ot_rate = [budget_dl_ot_rate] * 4 + [new_dl_ot_rate] * 8 
actual_dl_ot_hours = [0] * 12

actual_standard_times = [budget_standard_time] * 10 + [new_standard_time] + [budget_standard_time]


for i in range(12):
    total_hours_needed = actual_revenue_qty[i] * actual_standard_times[i]
    actual_dl_ot_hours[i] = round(max(0, total_hours_needed - regular_hours),2)

actual_dl_reg_amount = [actual_dl_reg_rate[i] * regular_hours for i in range(12)]
actual_dl_ot_amount = [actual_dl_ot_hours[i] * actual_dl_ot_rate[i]  for i in range(12)]


"""
Actual repair & maintence
Normal months: +/-3% noise. 
"""

actual_rm_maint = [0] * 12

for i in range(12):
    noise = np.random.uniform(-0.03, 0.03)
    if i == 0:  
        actual_rm_maint[i] = budget_rm_maint[i] * (1 + noise) + emergency_repair
    elif i == 7:  
        actual_rm_maint[i] = budget_rm_maint[i] * (1 + noise) - reduced_repair
    else:
        actual_rm_maint[i] = budget_rm_maint[i] * (1 + noise)

actual_rm_maint = [round(x, 2) for x in actual_rm_maint]



"""
Actual inbound freight
"""

actual_freight_qty = []
actual_freight_price = [budget_freight_price] * 8 + [new_freight_price] * 4

for i in range(12):
    freight_q = math.ceil(actual_rm_qty[i]/ truck) 
    actual_freight_qty.append(freight_q)

actual_freight_amount = [actual_freight_qty[i] * actual_freight_price[i] for i in range(12)]


"""
Build fact table
"""

cost_center_map = {
    "Revenue": "Sales",
    "Raw Materials": "Production",
    "Direct Labor – Regular": "Production",
    "Direct Labor – Overtime": "Production",
    "Repairs & Maintenance": "Production",
    "Inbound Freight": "Inbound Logistics",
}

def build_fact(amounts_dict):
    rows = []
    for account, amounts in amounts_dict.items():
        for i in range(12):
            rows.append({
                "Date": DATES[i],
                "CostCenter": cost_center_map[account],
                "Account": account,
                "Amount": round(amounts[i], 2),
            })
    return pd.DataFrame(rows)

budget_amounts = {
    "Revenue": [budget_revenue_qty[i] * budget_revenue_price for i in range(12)],
    "Raw Materials": [budget_rm_qty[i] * budget_rm_price for i in range(12)],
    "Direct Labor – Regular": [budget_dl_reg_hours[i] * budget_dl_reg_rate for i in range(12)],
    "Direct Labor – Overtime": [budget_dl_ot_hours[i] * budget_dl_ot_rate for i in range(12)],
    "Repairs & Maintenance": budget_rm_maint,
    "Inbound Freight": [budget_freight_qty[i] * budget_freight_price for i in range(12)],
}

actual_amounts = {
    "Revenue": actual_revenue_amount,
    "Raw Materials": actual_rm_amount,
    "Direct Labor – Regular": actual_dl_reg_amount,
    "Direct Labor – Overtime": actual_dl_ot_amount,
    "Repairs & Maintenance": actual_rm_maint,
    "Inbound Freight": actual_freight_amount,
}

fact_budget = build_fact(budget_amounts)
fact_actual = build_fact(actual_amounts)


"""
Build driver table
"""

def build_driver_table(qty_price_specs, labor_spec, extra_metrics=None):
    rows = []
    for account, (cc, qty_list, price_list, qty_uom, price_uom) in qty_price_specs.items():
        for i in range(12):
            rows.append({"Date": DATES[i], "CostCenter": cc, "Account": account,
                         "DriverMetric": "Quantity", "DriverValue": qty_list[i], "UnitOfMeasure": qty_uom})
            
            rows.append({"Date": DATES[i], "CostCenter": cc, "Account": account,
                         "DriverMetric": "UnitPrice", "DriverValue": price_list[i], "UnitOfMeasure": price_uom})
            
    cc, reg_h, reg_r, ot_h, ot_r = labor_spec
    reg_r_list = reg_r if isinstance(reg_r, list) else [reg_r] * 12
    ot_r_list = ot_r if isinstance(ot_r, list) else [ot_r] * 12

    for i in range(12):
        rows.append({"Date": DATES[i], "CostCenter": cc, "Account": "Direct Labor – Regular",
                     "DriverMetric": "RegularHours", "DriverValue": reg_h[i], "UnitOfMeasure": "Hours"})
        
        rows.append({"Date": DATES[i], "CostCenter": cc, "Account": "Direct Labor – Regular",
                     "DriverMetric": "RegularRate", "DriverValue": reg_r_list[i], "UnitOfMeasure": "EUR/Hour"})
        
        rows.append({"Date": DATES[i], "CostCenter": cc, "Account": "Direct Labor – Overtime",
                     "DriverMetric": "OvertimeHours", "DriverValue": ot_h[i], "UnitOfMeasure": "Hours"})
        
        rows.append({"Date": DATES[i], "CostCenter": cc, "Account": "Direct Labor – Overtime",
                     "DriverMetric": "OvertimeRate", "DriverValue": ot_r_list[i], "UnitOfMeasure": "EUR/Hour"})
    if extra_metrics:
        for cc, account, metric_name, value_list, uom in extra_metrics:
            for i in range(12):
                rows.append({"Date": DATES[i], "CostCenter": cc, "Account": account,
                             "DriverMetric": metric_name, "DriverValue": value_list[i], "UnitOfMeasure": uom})
        
    return pd.DataFrame(rows)

budget_qty_price_specs = {
    "Revenue": ("Sales", budget_revenue_qty, [budget_revenue_price] * 12, "Units", "EUR/Unit"),
    "Raw Materials": ("Production", budget_rm_qty, [budget_rm_price] * 12, "Tons", "EUR/Ton"),
    "Inbound Freight": ("Inbound Logistics", budget_freight_qty, [budget_freight_price] * 12, "Trucks", "EUR/Truck"),
}

budget_labor_spec = ("Production", budget_dl_reg_hours, budget_dl_reg_rate, budget_dl_ot_hours, budget_dl_ot_rate)

actual_qty_price_specs = {
    "Revenue": ("Sales", actual_revenue_qty, actual_revenue_price, "Units", "EUR/Unit"),
    "Raw Materials": ("Production", actual_rm_qty, actual_rm_price, "Tons", "EUR/Ton"),
    "Inbound Freight": ("Inbound Logistics", actual_freight_qty, actual_freight_price, "Trucks", "EUR/Truck"),
}

actual_labor_spec = ("Production", actual_dl_reg_hours, actual_dl_reg_rate, actual_dl_ot_hours, actual_dl_ot_rate)


actual_rm_per_unit = [round(actual_rm_qty[i] / actual_revenue_qty[i],2) for i in range(12)]

budget_extra_metrics = [
    ("Production", "Raw Materials", "TonsPerUnit", [budget_rm_per_unit] * 12, "Ton/Unit"),
    ("Production", "Direct Labor – Regular", "HoursPerUnit", [budget_standard_time] * 12, "Hour/Unit"),
]


actual_extra_metrics = [
    ("Production", "Raw Materials", "TonsPerUnit", actual_rm_per_unit, "Ton/Unit"),
    ("Production", "Direct Labor – Regular", "HoursPerUnit", actual_standard_times, "Hour/Unit"),
]


known_events_rows = [
    {"Date": DATES[0], "CostCenter": "Sales", "Account": "Revenue",
     "DriverMetric": "KnownEvent", "DriverValue": -shortfall_units, "UnitOfMeasure": "Units"},
    {"Date": DATES[2], "CostCenter": "Sales", "Account": "Revenue",
     "DriverMetric": "KnownEvent", "DriverValue": add_units, "UnitOfMeasure": "Units"},
    {"Date": DATES[0], "CostCenter": "Production", "Account": "Repairs & Maintenance",
     "DriverMetric": "KnownEvent", "DriverValue": emergency_repair, "UnitOfMeasure": "EUR"},
    {"Date": DATES[7], "CostCenter": "Production", "Account": "Repairs & Maintenance",
     "DriverMetric": "KnownEvent", "DriverValue": -reduced_repair, "UnitOfMeasure": "EUR"},
]


fact_budget_driver = build_driver_table(budget_qty_price_specs, budget_labor_spec, budget_extra_metrics)
fact_actual_driver = build_driver_table(actual_qty_price_specs, actual_labor_spec, actual_extra_metrics)
fact_actual_driver = pd.concat([fact_actual_driver, pd.DataFrame(known_events_rows)], ignore_index=True)

assumptions = pd.DataFrame([ 
    {"Parameter": "Workers", "Value": workers, "UnitOfMeasure": "Headcount", "Account": "Direct Labor – Regular"},
    {"Parameter": "TruckCapacity", "Value": truck, "UnitOfMeasure": "Ton/Truck", "Account": "Inbound Freight"},
])


costcenter = pd.DataFrame([
    {"CostCenter": "Sales", "Account": "Revenue", "AccountType": "Revenue"},
    {"CostCenter": "Production", "Account": "Raw Materials", "AccountType": "Cost"},
    {"CostCenter": "Production", "Account": "Direct Labor – Regular", "AccountType": "Cost"},
    {"CostCenter": "Production", "Account": "Direct Labor – Overtime", "AccountType": "Cost"},
    {"CostCenter": "Production", "Account": "Repairs & Maintenance", "AccountType": "Cost"},
    {"CostCenter": "Inbound Logistics", "Account": "Inbound Freight", "AccountType": "Cost"},
])

"""
Export
"""

with pd.ExcelWriter(f"{OUT_DIR}/Budget_Actual.xlsx", engine="openpyxl") as writer:
    fact_budget.to_excel(writer, sheet_name="Fact_Budget", index=False)
    fact_actual.to_excel(writer, sheet_name="Fact_Actual", index=False)
    fact_budget_driver.to_excel(writer, sheet_name="Budget_Drivers", index=False)
    fact_actual_driver.to_excel(writer, sheet_name="Actual_Drivers", index=False)
    costcenter.to_excel(writer, sheet_name="Cost Center", index=False)
    assumptions.to_excel(writer, sheet_name="Assumptions", index=False)


"""
Details
"""

summary = fact_budget.groupby("Account")["Amount"].sum().rename("Budget_Total").to_frame()
summary["Actual_Total"] = fact_actual.groupby("Account")["Amount"].sum()
summary["Variance"] = summary["Actual_Total"] - summary["Budget_Total"]
summary["Variance %"] = round((summary["Variance"] / summary["Budget_Total"] * 100), 2)
print(summary)


