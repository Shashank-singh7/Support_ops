# generate_data.py
import csv, json, random, string, os
from datetime import datetime, timedelta

SEED = 42
random.seed(SEED)

N_TICKETS = 5000
N_CUSTOMERS = 250
START_DATE = datetime(2025, 1, 1)
DAYS = 180

CATEGORIES = ["Billing", "Login", "Bug", "Feature", "Performance", "Integration", "Security"]
CHANNELS = ["email", "chat", "phone", "web"]
PRIORITIES = ["low", "medium", "high", "urgent"]
REGIONS = ["NA", "EU", "APAC", "LATAM"]
PLANS = ["free", "pro", "business", "enterprise"]

SLA_HOURS = {"low": 36, "medium": 24, "high": 12, "urgent": 4}

def rid(prefix, n=8):
    return prefix + "".join(random.choices(string.ascii_uppercase + string.digits, k=n))

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

# Customers
customers = []
for _ in range(N_CUSTOMERS):
    customers.append({
        "customer_id": rid("C_"),
        "region": random.choices(REGIONS, weights=[40, 25, 25, 10])[0],
        "plan": random.choices(PLANS, weights=[35, 35, 20, 10])[0],
        "tenure_months": int(clamp(random.gauss(18, 10), 0, 60)),
        "employees": int(clamp(random.lognormvariate(3.2, 0.7), 1, 5000)),
    })

os.makedirs("data", exist_ok=True)

sla_policy = {"sla_hours_by_priority": SLA_HOURS}
with open("data/sla_policy.json", "w") as f:
    json.dump(sla_policy, f, indent=2)

rows = []

for _ in range(N_TICKETS):
    customer = random.choice(customers)

    created_at = START_DATE + timedelta(
        days=random.randint(0, DAYS-1),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )

    category = random.choice(CATEGORIES)
    channel = random.choice(CHANNELS)
    priority = random.choice(PRIORITIES)

    base_difficulty = {
        "Billing": 0.4,
        "Login": 0.5,
        "Bug": 0.7,
        "Feature": 0.8,
        "Performance": 0.75,
        "Integration": 0.8,
        "Security": 0.9
    }[category]

    plan = customer["plan"]
    region = customer["region"]

    pri_factor = {"low": 1.4, "medium": 1.1, "high": 0.9, "urgent": 0.6}[priority]
    plan_factor = {"free": 1.3, "pro": 1.1, "business": 0.9, "enterprise": 0.75}[plan]
    chan_factor = {"email": 1.1, "chat": 0.8, "phone": 0.7, "web": 1.0}[channel]
    region_factor = {"NA": 0.95, "EU": 1.0, "APAC": 1.05, "LATAM": 1.1}[region]

    noise = random.lognormvariate(0, 0.5)

    first_response_hours = (
        12 * base_difficulty
        * pri_factor
        * plan_factor
        * chan_factor
        * region_factor
        * noise
    )

    first_response_hours = clamp(first_response_hours, 0.1, 120)

    # Initial SLA check
    sla = SLA_HOURS[priority]
    breached = 1 if first_response_hours > sla else 0

    # 🔥 Force breached tickets to be urgent
    if breached == 1:
        priority = "urgent"
        sla = SLA_HOURS["urgent"]
        breached = 1 if first_response_hours > sla else 0

    is_open = 1 if random.random() < 0.06 else 0
    resolution_hours = None

    if not is_open:
        res_noise = random.lognormvariate(0, 0.6)
        resolution_hours = clamp(
            (first_response_hours * 0.7 + 12 * base_difficulty) * res_noise,
            0.2,
            500
        )

    summary = random.choice([
        "Invoice mismatch", "Refund request", "App crash",
        "Request export option", "Slow dashboard",
        "Webhook failing", "Suspicious login"
    ])

    # Dirty data injection
    if random.random() < 0.01:
        priority = "med"

    if random.random() < 0.01:
        first_response_hours = ""

    if random.random() < 0.005:
        created_at = ""

    rows.append({
        "ticket_id": rid("T_"),
        "customer_id": customer["customer_id"],
        "created_at": created_at if isinstance(created_at, str) else created_at.isoformat(),
        "category": category,
        "channel": channel,
        "priority": priority,
        "first_response_time_hours": first_response_hours,
        "resolution_time_hours": resolution_hours,
        "is_open": is_open,
        "breached_sla": breached,
        "summary": summary
    })

with open("data/customers.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(customers[0].keys()))
    w.writeheader()
    w.writerows(customers)

with open("data/tickets.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

print("Wrote: tickets.csv, customers.csv, sla_policy.json")
