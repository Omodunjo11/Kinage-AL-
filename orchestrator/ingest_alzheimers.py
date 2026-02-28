import feedparser
from orchestrator.al_sources import ALZHEIMERS_FEEDS
from orchestrator.ingest_core import ingest_feed  # adjust if needed


def ingest_alzheimers():
    print("Ingesting Alzheimer-related feeds...")

    for source_name, url in ALZHEIMERS_FEEDS.items():
        print(f"Fetching {source_name}...")
        ingest_feed(
            source_name=source_name,
            url=url,
            default_domain="Cognitive Decline"
        )

    print("Alzheimer ingestion complete.")


if __name__ == "__main__":
    ingest_alzheimers()
