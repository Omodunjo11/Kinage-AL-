"""
AL — Intelligence briefing summary generation.
Pre-computed, deterministic, cached in corpus JSON. Not runtime-generated.
Uses gpt-4o-mini, temp 0.3, first 4000 chars. Only run for chunks above score threshold.
"""

import os
import json
import yaml
from pathlib import Path
from openai import OpenAI

BASE = Path(__file__).resolve().parent.parent
with open(BASE / "config" / "config.yaml") as f:
    _cfg = yaml.safe_load(f)

_api_key = os.getenv("OPENAI_API_KEY")
_client = OpenAI(api_key=_api_key) if _api_key else None

SUMMARY_MODEL = (_cfg.get("llm") or {}).get("summary_model", "gpt-4o-mini")
SUMMARY_TEMPERATURE = 0.3
MAX_INPUT_CHARS = 4000

# Map taxonomy domain tags to Kinage briefing context
DOMAIN_TO_KINAGE_CONTEXT = {
    "bill_execution": "seniors, bill execution, missed payments, administrative fragmentation",
    "family_coordination": "family coordination, remote caregiving, role clarity, financial responsibility",
    "fraud_exploitation": "fraud risk, elder scams, financial exploitation",
    "cognitive_decline": "cognitive decline, dementia, financial vulnerability",
    "regulatory_enforcement": "FTC/DOJ enforcement, regulatory implications",
    "influence_channels": "purchase-decision media, channel influence",
}


def _domain_context(dominant_domain: str) -> str:
    if not dominant_domain:
        return "seniors, bill execution, fraud risk, or family coordination"
    return DOMAIN_TO_KINAGE_CONTEXT.get(
        dominant_domain.strip().lower(),
        dominant_domain,
    )


def generate_summary(article_text: str, dominant_domain: str = "") -> dict:
    """
    Generate structured intelligence briefing for a chunk.
    Returns dict with: summary, why_it_matters, risk_type, entities, severity.
    """
    if not _client:
        return _fallback_summary(article_text, dominant_domain)

    text_slice = (article_text or "")[:MAX_INPUT_CHARS]
    context = _domain_context(dominant_domain)

    prompt = f"""Return JSON only. No markdown, no explanation.

{{
  "summary": "Executive summary in 3 sentences max.",
  "why_it_matters": "1-2 sentences on why this matters for Kinage: {context}.",
  "risk_type": "One of: Fraud | Cognitive | Execution | Coordination",
  "entities": ["List", "of", "named", "entities", "e.g. FTC", "Bank of America"],
  "severity": "One of: Low | Moderate | Elevated | Critical"
}}

Article:
{text_slice}

Domain context: {context}
"""

    try:
        response = _client.chat.completions.create(
            model=SUMMARY_MODEL,
            temperature=SUMMARY_TEMPERATURE,
            max_tokens=500,
            messages=[
                {"role": "system", "content": "You are a financial risk intelligence analyst. Output valid JSON only."},
                {"role": "user", "content": prompt},
            ],
        )
        raw = (response.choices[0].message.content or "").strip()
        # Strip markdown code fence if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]
        parsed = json.loads(raw)

        return {
            "summary": parsed.get("summary", ""),
            "why_it_matters": parsed.get("why_it_matters", ""),
            "risk_type": parsed.get("risk_type", ""),
            "entities": parsed.get("entities") if isinstance(parsed.get("entities"), list) else [],
            "severity": parsed.get("severity", ""),
        }
    except Exception:
        return _fallback_summary(article_text, dominant_domain)


def _fallback_summary(article_text: str, dominant_domain: str) -> dict:
    """When API is unavailable or parsing fails."""
    text = (article_text or "")[:500]
    return {
        "summary": text[:300] + ("..." if len(text) > 300 else ""),
        "why_it_matters": f"Relevant to Kinage domain: {dominant_domain or 'general'}.",
        "risk_type": "",
        "entities": [],
        "severity": "Low",
    }
