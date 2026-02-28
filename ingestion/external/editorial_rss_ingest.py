import feedparser
from datetime import datetime

EDITORIAL_FEEDS = [
    {
        "name": "NYT Wirecutter",
        "url": "https://www.nytimes.com/wirecutter/feed/",
        "authority_weight": 1.2,
        "domain_tag": "influence_channels"
    },
    {
        "name": "Caring.com Caregivers",
        "url": "https://www.caring.com/caregivers/feed/",
        "authority_weight": 1.1,
        "domain_tag": "influence_channels"
    }
]


def fetch_feed(feed_config):
    feed = feedparser.parse(feed_config["url"])
    items = []

    for entry in feed.entries[:20]:
        content = f"""
        Source: {feed_config['name']}
        Title: {entry.get('title', '')}
        Published: {entry.get('published', '')}
        Link: {entry.get('link', '')}

        Summary:
        {entry.get('summary', '')}
        """

        metadata = {
            "source": feed_config["name"],
            "authority_weight": feed_config["authority_weight"],
            "domain_tag": feed_config["domain_tag"],
            "publish_date": entry.get("published", ""),
            "link": entry.get("link", "")
        }

        items.append((content, metadata))

    return items


if __name__ == "__main__":
    all_items = []

    for feed in EDITORIAL_FEEDS:
        items = fetch_feed(feed)
        all_items.extend(items)

    print(f"Fetched {len(all_items)} editorial articles.")

from utils.embedding_helper import embed_and_store  # adjust if your helper name differs


if __name__ == "__main__":
    all_items = []

    for feed in EDITORIAL_FEEDS:
        items = fetch_feed(feed)
        all_items.extend(items)

    print(f"Fetched {len(all_items)} editorial articles.")

    for content, metadata in all_items:
        embed_and_store(
            text=content,
            metadata=metadata,
            index_name="external"
        )

    print("Editorial articles embedded and stored.")
