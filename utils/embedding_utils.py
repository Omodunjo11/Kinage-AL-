import os
import numpy as np
from openai import OpenAI
import yaml

# Load config (non-secret settings only)
with open("config/config.yaml") as f:
    cfg = yaml.safe_load(f)

# Load API key securely from environment
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables.")

client = OpenAI(api_key=api_key)

EMBED_MODEL = cfg["embeddings"]["model"]

def embed_text(text: str):
    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=text
    )
    return np.array(response.data[0].embedding)

def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (
        np.linalg.norm(vec1) * np.linalg.norm(vec2)
    )
