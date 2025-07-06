# === Accounting Logic ===

from flask import jsonify

def get_accounting_summary():
    return jsonify({
        "budget_vs_actual": [
            {"category": "Labor", "budget": 50000, "actual": 46000},
            {"category": "Materials", "budget": 80000, "actual": 82000},
            {"category": "Transport", "budget": 10000, "actual": 7500}
        ],
        "monthly_expense": [
            {"month": "Jan", "amount": 12000},
            {"month": "Feb", "amount": 15000},
            {"month": "Mar", "amount": 9800},
            {"month": "Apr", "amount": 17500}
        ]
    })
