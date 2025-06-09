from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from sentence_transformers import SentenceTransformer
from collections import defaultdict
import requests
import os

# CONFIG
COLLECTION_NAME = "mtg_rules"
EMBED_MODEL = "all-MiniLM-L6-v2"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
HF_MODEL = "meta-llama/Llama-3.1-8B-Instruct"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HEADERS = {"Authorization": f"Bearer {HF_API_TOKEN}"}
TOP_K = 5

embedder = SentenceTransformer(EMBED_MODEL)
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

def search_with_expansion(query):
    query_vec = embedder.encode(query)
    hits = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vec,
        limit=TOP_K,
        with_payload=True
    )

    grouped = defaultdict(list)
    for pt in hits.points:
        grouped[pt.payload["rule_group"]].append(pt.payload)

    # Build Qdrant filter
    filter_ = qmodels.Filter(
        should=[
            qmodels.FieldCondition(
                key="rule_group",
                match=qmodels.MatchValue(value=group)
            )
            for group in grouped
        ]
    )

    expanded, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=filter_,
        limit=100,
        with_payload=True
    )

    unique = {pt.payload["rule_number"]: pt.payload for pt in expanded}
    return [unique[k] for k in sorted(unique)]

def build_prompt(rules, question):
    parts = []
    for r in rules:
        rule_text = f"{r['rule_number']}: {r['text']}"
        if "examples" in r and r["examples"]:
            example_text = "\n".join(f"    {ex}" for ex in r["examples"])
            rule_text += f"\n  Examples:\n{example_text}"
        parts.append(rule_text)

    content = "\n\n".join(parts)
    return f"""You are a Magic: The Gathering rules judge.

Use the following rules and examples to answer the player's question accurately.

Rules:
{content}

Question:
{question}

Answer:"""


def call_llama(prompt):
    res = requests.post(
        HF_API_URL,
        headers=HEADERS,
        json={
            "inputs": prompt,
            "parameters": {"max_new_tokens": 300, "temperature": 0.3}
        }
    )
    res.raise_for_status()
    return res.json()[0]["generated_text"]

def answer_question(q):
    rules = search_with_expansion(q)
    prompt = build_prompt(rules, q)
    return call_llama(prompt)

if __name__=="__main__":
    while True:
        q = input("Q> ")
        if q.strip().lower() in ("exit","quit"):
            break
        print(answer_question(q))
