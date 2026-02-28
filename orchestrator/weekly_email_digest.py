"""
Kinage SignifAL — Intelligence Newsletter Engine

Behavior:
• First run: sends ALL currently ingested articles
• Future runs: sends ONLY new articles
• No recency filtering
• Domain-based semantic clustering
• Tracks sent articles to prevent duplicates
"""

from pathlib import Path
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

from utils.semantic_domain_scorer import compute_total_signal


# -------------------------------------------------
# Environment + Paths
# -------------------------------------------------

BASE = Path(__file__).resolve().parent.parent
load_dotenv(BASE / ".env")

RSS_DIR = BASE / "corpus" / "external" / "rss"
SENT_REGISTRY_PATH = BASE / "outputs" / "sent_articles.json"


# -------------------------------------------------
# Domain Display Labels (External-Facing)
# -------------------------------------------------

DOMAIN_LABELS = {
    "DOMAIN_A": "Bill Execution & Administrative Breakdown",
    "DOMAIN_B": "Family Financial Coordination & Authority",
    "DOMAIN_C": "Fraud, Exploitation & Financial Abuse",
    "DOMAIN_D": "Cognitive Decline & Financial Vulnerability",
    "DOMAIN_E": "Dignity, Autonomy & Financial Control",
    "DOMAIN_F": "Market Movement & Vendor Landscape"
}


# -------------------------------------------------
# Sent Registry Helpers
# -------------------------------------------------

def load_sent_registry():
    if not SENT_REGISTRY_PATH.exists():
        return {"sent_ids": []}

    with open(SENT_REGISTRY_PATH) as f:
        return json.load(f)


def save_sent_registry(registry):
    with open(SENT_REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)


# -------------------------------------------------
# Load RSS Articles
# -------------------------------------------------

def load_chunks():

    if not RSS_DIR.exists():
        print("RSS directory not found.")
        return []

    chunks = []

    for file in RSS_DIR.glob("*.json"):
        try:
            with open(file) as f:
                data = json.load(f)

                # Use filename as canonical ID
                data["_file_id"] = file.name
                chunks.append(data)

        except Exception as e:
            print(f"Error loading {file.name}: {e}")

    print(f"Total RSS files loaded: {len(chunks)}")
    return chunks


# -------------------------------------------------
# Filter Unsent Articles
# -------------------------------------------------

def filter_unsent(chunks):

    registry = load_sent_registry()
    sent_ids = set(registry.get("sent_ids", []))

    unsent = []

    for chunk in chunks:
        chunk_id = chunk.get("_file_id")
        if chunk_id and chunk_id not in sent_ids:
            unsent.append(chunk)

    print(f"Unsent articles found: {len(unsent)}")
    return unsent, registry


# -------------------------------------------------
# Semantic Scoring + Domain Grouping
# -------------------------------------------------

def score_and_group(items):

    domain_groups = {}

    for item in items:

        text = item.get("text", "")
        if not text:
            continue

        total_score, raw_domains = compute_total_signal(text)

        item["semantic_score"] = total_score
        item["raw_domains"] = raw_domains

        dominant = max(raw_domains, key=raw_domains.get)
        item["dominant_domain"] = dominant

        if dominant not in domain_groups:
            domain_groups[dominant] = []

        domain_groups[dominant].append(item)

    # Sort articles within each domain
    for domain in domain_groups:
        domain_groups[domain].sort(
            key=lambda x: x["semantic_score"],
            reverse=True
        )

        print(f"{domain}: {len(domain_groups[domain])} articles")

    return domain_groups


# -------------------------------------------------
# Build Email HTML
# -------------------------------------------------

def build_email_html(domain_groups):

    html = """
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;
                 background:#f6f8fa; padding:40px;">
        <div style="max-width:950px; margin:auto; background:white; padding:50px; border-radius:14px;">
            <h1>Kinage SignifAL Intelligence Update</h1>
            <p style="color:#666;">Strategic Monitoring Across Execution, Coordination, Fraud & Capacity Risk</p>
            <hr style="margin:30px 0;">
    """

    for domain, items in domain_groups.items():

        display_label = DOMAIN_LABELS.get(domain, domain)

        html += f"""
        <h2 style="margin-top:40px; border-bottom:1px solid #eee; padding-bottom:10px;">
            {display_label}
        </h2>
        """

        for item in items:

            metadata = item.get("metadata", {})
            title = metadata.get("title", "Untitled")
            url = metadata.get("url", "#")
            score = round(item.get("semantic_score", 0), 3)

            html += f"""
            <div style="margin-bottom:25px;">
                <strong style="font-size:16px;">{title}</strong><br>
                <span style="font-size:12px; color:#888;">
                    Strategic Signal Score: {score}
                </span><br>
                <a href="{url}" style="color:#0A66C2; text-decoration:none;">
                    Read Article →
                </a>
            </div>
            """

    html += """
            <hr style="margin-top:50px;">
            <p style="font-size:12px; color:#aaa;">
                Generated by Kinage SignifAL Intelligence Engine
            </p>
        </div>
    </body>
    </html>
    """

    return html


# -------------------------------------------------
# Send Email
# -------------------------------------------------

def send_email(html_content):

    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    recipient = os.getenv("EMAIL_RECIPIENT")

    if not sender or not password or not recipient:
        print("Missing email credentials.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Kinage SignifAL Intelligence Update"
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.send_message(msg)

        print("Email sent successfully.")
        return True

    except Exception as e:
        print(f"Error sending email: {e}")
        return False


# -------------------------------------------------
# Main
# -------------------------------------------------

def main():

    print("── Generating Kinage SignifAL Intelligence ──")

    chunks = load_chunks()
    if not chunks:
        print("No RSS articles found.")
        return

    unsent_chunks, registry = filter_unsent(chunks)

    if not unsent_chunks:
        print("No new articles to send.")
        return

    domain_groups = score_and_group(unsent_chunks)

    html = build_email_html(domain_groups)

    sent_successfully = send_email(html)

    if sent_successfully:
        new_ids = [chunk["_file_id"] for chunk in unsent_chunks]
        registry["sent_ids"].extend(new_ids)
        save_sent_registry(registry)
        print(f"Marked {len(new_ids)} articles as sent.")


if __name__ == "__main__":
    main()
