import requests
import json

BASE_URL = "http://127.0.0.1:5001"

scenarios = [
    {
        "name": "High Risk (Security/Urgent/Email)",
        "data": {
            "category": "Security",
            "priority": "urgent",
            "channel": "email",
            "region": "NA", "plan": "pro", "tenure_months": 12, "employees": 100
        },
        "expected": "High Probability (>50%)"
    },
    {
        "name": "Moderate Risk (Integration/High/Web)",
        "data": {
            "category": "Integration",
            "priority": "high",
            "channel": "web",
            "region": "NA", "plan": "pro", "tenure_months": 12, "employees": 100
        },
        "expected": "Moderate (~30-60%)"
    },
    {
        "name": "Safe (Billing/Low/Chat)",
        "data": {
            "category": "Billing",
            "priority": "low",
            "channel": "chat",
            "region": "NA", "plan": "pro", "tenure_months": 12, "employees": 100
        },
        "expected": "Low Probability (<20%)"
    },
    {
        "name": "Safe (Login/Medium/Phone)",
        "data": {
            "category": "Login",
            "priority": "medium",
            "channel": "phone",
            "region": "NA", "plan": "pro", "tenure_months": 12, "employees": 100
        },
        "expected": "Low Probability (<20%)"
    }
]

print(f"{'Scenario':<40} | {'Prob':<10} | {'Label':<10} | {'Expected'}")
print("-" * 80)

for sc in scenarios:
    try:
        response = requests.post(f"{BASE_URL}/predict", json=sc["data"])
        if response.status_code == 200:
            res = response.json()
            prob = res['probability'] * 100
            label = "BREACH" if res['label'] == 1 else "SAFE"
            print(f"{sc['name']:<40} | {prob:5.1f}%    | {label:<10} | {sc['expected']}")
        else:
            print(f"{sc['name']:<40} | ERROR {response.status_code}")
    except Exception as e:
         print(f"{sc['name']:<40} | FAILED: {str(e)}")
