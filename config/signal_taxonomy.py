# config/signal_taxonomy.py

TAXONOMY = {
    "DOMAIN_A": {
        "name": "Bill Execution & Administrative Control",
        "weight": 0.60,
        "clusters": {
            "A1_Missed_Late_Disrupted": [
                "missed bill elderly",
                "unpaid utilities senior",
                "late fees aging parent",
                "bill overdue confusion",
                "service shutoff nonpayment"
            ],
            "A2_Duplicate_Irregular": [
                "duplicate payment elderly",
                "double paid bill",
                "incorrect charge parent",
                "overpayment utilities",
                "subscription confusion senior"
            ],
            "A3_Fragmentation": [
                "paper bills everywhere",
                "too many bank accounts parent",
                "managing bills for parents",
                "tracking bills manually",
                "spreadsheet bill tracker"
            ],
            "A4_Automation_Tools": [
                "automated bill detection",
                "bill management software senior",
                "family bill dashboard",
                "payment coordination app",
                "financial oversight platform"
            ],
        },
    },

    "DOMAIN_B": {
        "name": "Family Coordination & Role Clarity",
        "weight": 0.50,
        "clusters": {
            "B1_Role_Conflict": [
                "who is paying the bills",
                "sibling conflict money",
                "family disagreement finances",
                "unclear responsibility parent bills",
                "shared financial access confusion"
            ],
            "B2_Remote_Oversight": [
                "managing parents finances remotely",
                "long distance caregiver bills",
                "accessing parents accounts emergency",
                "remote financial coordination"
            ],
            "B3_Control_Transitions": [
                "when to take over finances",
                "stepping in financially parent",
                "power of attorney timing",
                "financial guardianship transition"
            ],
        },
    },

    "DOMAIN_C": {
        "name": "Fraud & Exploitation",
        "weight": 0.30,
        "clusters": {
            "C1_External_Scams": [
                "elder scam",
                "senior fraud",
                "phishing elderly",
                "romance scam senior",
                "IRS scam parent"
            ],
            "C2_Internal_Abuse": [
                "power of attorney abuse",
                "caregiver theft",
                "financial abuse elderly",
                "guardianship misuse"
            ],
            "C3_Fraud_Monitoring": [
                "fraud monitoring tools",
                "suspicious transaction alert",
                "elder fraud prevention software"
            ],
        },
    },

    "DOMAIN_D": {
        "name": "Cognitive Decline & Vulnerability",
        "weight": 0.25,
        "clusters": {
            "D1_Dementia_Financial_Errors": [
                "dementia finances",
                "forgetting to pay bills elderly",
                "memory loss money mistakes",
                "financial capacity decline"
            ],
            "D2_Behavioral_Anomalies": [
                "unusual spending elderly",
                "financial confusion memory",
                "cognitive decline bill mistakes"
            ],
        },
    },
}
