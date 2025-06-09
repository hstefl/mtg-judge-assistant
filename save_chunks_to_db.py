from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from sentence_transformers import SentenceTransformer
import json
import hashlib

# === CONFIG ===
COLLECTION_NAME = "mtg_rules"
RULE_JSON_PATH = "per_rule_chunks.json"
MODEL_NAME = "all-MiniLM-L6-v2"
VECTOR_DIM = 384  # Based on the embedding model (above)

# === INIT CLIENTS ===
client = QdrantClient(host="localhost", port=6333)
model = SentenceTransformer(MODEL_NAME)

# === CREATE COLLECTION ===
client.recreate_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=qmodels.VectorParams(
        size=VECTOR_DIM,
        distance=qmodels.Distance.COSINE
    )
)

# === LOAD RULES ===
with open(RULE_JSON_PATH, encoding="utf-8") as f:
    rules = json.load(f)

# === PREPARE POINTS ===
points = []
for rule in rules:
    rule_text = rule["text"]
    vector = model.encode(rule_text)
    point_id = hashlib.md5(rule_text.encode()).hexdigest()

    points.append(qmodels.PointStruct(
        id=point_id,
        vector=vector.tolist(),
        payload={
            "rule_number": rule["rule_number"],
            "rule_group": rule["rule_group"],
            "rule_root": rule["rule_root"],
            "text": rule_text,
            "source_doc": rule["source_doc"]
        }
    ))

# === INSERT ===
print(f"Uploading {len(points)} rules to Qdrant...")
client.upsert(collection_name=COLLECTION_NAME, points=points)
print("✅ Done.")
