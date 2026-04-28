DOMAIN_SEMANTICS = {
    # Updated: 2026-04-28
    # These descriptions are embedded and used for semantic scoring.

    "DOMAIN_A": {
        "weight": 0.55,
        "description": """
        Bills and payment execution for older adults and families:
        missed payments, late fees, autopay failures, insufficient funds,
        duplicate payments, recurring charge confusion, utilities and medical bills,
        and workflows/tools that prevent bills from falling through the cracks.
        """,
    },
    "DOMAIN_B": {
        "weight": 0.50,
        "description": """
        Family and caregiver coordination around day-to-day finances:
        shared visibility, assigning responsibilities, audit trails,
        remote caregiving oversight, sibling handoffs, and role clarity
        while keeping the older adult in control.
        """,
    },
    "DOMAIN_C": {
        "weight": 0.35,
        "description": """
        Fraud, scams, and financial exploitation targeting older adults:
        impersonation scams, gift card fraud, phishing, identity theft,
        account takeover, suspicious vendors/charges, POA abuse,
        and consumer protection / enforcement actions.
        """,
    },
    "DOMAIN_D": {
        "weight": 0.30,
        "description": """
        Cognitive decline and financial vulnerability:
        dementia-related bill mistakes, memory issues affecting decisions,
        diminished capacity, and safeguards to reduce harm without stripping autonomy.
        """,
    },
    "DOMAIN_E": {
        "weight": 0.25,
        "description": """
        Dignity, autonomy, and independence by design:
        privacy-preserving oversight, consent-based sharing,
        read-only access patterns, and designs that keep older adults in control
        while families/advisors provide a safety net.
        """,
    },
    "DOMAIN_F": {
        "weight": 0.15,
        "description": """
        Competitor and adjacent vendor/category signals:
        bill pay tools, fraud monitoring products, eldercare fintech,
        banking features, and market moves that change expectations.
        """,
    },
    "DOMAIN_G": {
        "weight": 0.20,
        "description": """
        Professional channel signals:
        Daily Money Managers, financial advisors, elder law attorneys,
        care managers, employers/benefits, and the workflows/reporting
        they need to support families.
        """,
    },
}
