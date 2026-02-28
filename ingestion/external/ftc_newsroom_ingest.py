import requests
from bs4 import BeautifulSoup
from datetime import datetime

FTC_NEWS_URL = "https://www.ftc.gov/news-events/news/press-releases"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def fetch_ftc_news():
    try:
        response = requests.get(FTC_NEWS_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"⚠ FTC fetch error: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    articles = []

    # FTC press releases are in article cards
    cards = soup.select("div.views-row")

    for card in cards[:15]:
        title_tag = card.find("a")
        date_tag = card.find("time")

        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        link = "https://www.ftc.gov" + title_tag.get("href", "")

        publish_date = ""
        if date_tag:
            publish_date = date_tag.get_text(strip=True)

        content = f"""
        Source: FTC Newsroom
        Title: {title}
        Published: {publish_date}
        Link: {link}
        """

        metadata = {
            "source": "FTC Newsroom",
            "authority_weight": 1.3,
            "domain_tag": "regulatory_enforcement",
            "publish_date": publish_date,
            "url": link
        }

        articles.append({
            "content": content,
            "metadata": metadata
        })

    return articles


def ingest_ftc_news():
    print("\n── FTC Newsroom ──")

    articles = fetch_ftc_news()

    print(f"{len(articles)} articles found\n")

    for article in articles[:5]:
        print(article["metadata"]["publish_date"])
        print(article["metadata"]["url"])
        print("-" * 60)

    return articles


if __name__ == "__main__":
    ingest_ftc_news()
