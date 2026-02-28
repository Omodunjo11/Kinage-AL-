import requests
from datetime import datetime, timedelta

# FTC enforcement dataset via data.gov CKAN API
FTC_DATASET_URL = "https://catalog.data.gov/api/3/action/package_search"

SEARCH_QUERY = "federal trade commission enforcement"

DAYS_BACK = 90


def fetch_ftc_enforcement_metadata():
    params = {
        "q": SEARCH_QUERY,
        "rows": 5
    }

    response = requests.get(FTC_DATASET_URL, params=params)

    if response.status_code != 200:
        print(f"⚠ HTTP {response.status_code}")
        return []

    data = response.json()

    results = data.get("result", {}).get("results", [])

    datasets = []

    for item in results:
        datasets.append({
            "title": item.get("title"),
            "organization": item.get("organization", {}).get("title"),
            "metadata_modified": item.get("metadata_modified"),
            "url": item.get("url"),
        })

    return datasets


def ingest_ftc_enforcement():
    print("\n── FTC Enforcement (Data.gov API) ──")

    datasets = fetch_ftc_enforcement_metadata()

    print(f"\n  {len(datasets)} datasets found\n")

    for ds in datasets:
        print(ds["title"])
        print(ds["organization"])
        print(ds["url"])
        print("-" * 40)

    return datasets


if __name__ == "__main__":
    ingest_ftc_enforcement()
