import requests
from datetime import datetime, timedelta

BASE_URL = "https://www.federalregister.gov/api/v1/documents.json"

SEARCH_TERMS = [
    "consumer fraud",
    "financial exploitation",
    "elder financial abuse",
    "financial protection",
]

DAYS_BACK = 90

AGENCIES = [
    "federal-trade-commission",
    "consumer-financial-protection-bureau"
]


def fetch_for_keyword(keyword):
    date_from = (datetime.utcnow() - timedelta(days=DAYS_BACK)).strftime("%Y-%m-%d")

    params = {
        "conditions[term]": keyword,
        "conditions[publication_date][gte]": date_from,
        "conditions[agencies][]": AGENCIES,
        "per_page": 50,
        "order": "newest",
    }

    response = requests.get(BASE_URL, params=params)

    if response.status_code != 200:
        print(f"  ⚠ {response.status_code} for '{keyword}'")
        return []

    return response.json().get("results", [])


def fetch_documents():
    all_docs = []
    seen = set()

    for keyword in SEARCH_TERMS:
        print(f"Querying: {keyword}")
        docs = fetch_for_keyword(keyword)

        for doc in docs:
            doc_id = doc.get("document_number")
            if doc_id not in seen:
                seen.add(doc_id)
                all_docs.append(doc)

    return all_docs


def ingest_federal_register():
    print("\n── Federal Register ──")

    docs = fetch_documents()

    print(f"\n  {len(docs)} unique documents found\n")

    for doc in docs[:10]:
        print(doc.get("title"))
        print(doc.get("html_url"))
        print("-" * 40)

    return docs


if __name__ == "__main__":
    ingest_federal_register()
