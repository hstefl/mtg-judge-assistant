import json
import os
import re

import requests
from bs4 import BeautifulSoup

# === CONFIGURATION ===
RULES_URL = "https://magic.wizards.com/en/rules"
DOWNLOAD_DIR = "downloads"
OUTPUT_DIR = "output"
OUTPUT_RULES_JSON = OUTPUT_DIR + "/per_rule_chunks.json"
OUTPUT_GLOSSARY_JSON = OUTPUT_DIR + "/glossary_chunks.json"
SOURCE_DOC_PREFIX = "CompRules_"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# === HELPERS ===

def get_latest_rules_txt_url():
    """Find the first .txt link on the rules page."""
    response = requests.get(RULES_URL)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    txt_links = [a["href"] for a in soup.find_all("a", href=True) if a["href"].lower().endswith(".txt")]
    if not txt_links:
        raise Exception("No .txt rule links found.")
    return txt_links[0]


def download_file_if_new(url, download_dir):
    filename = url.split("/")[-1]
    filepath = os.path.join(download_dir, filename)
    if os.path.exists(filepath):
        print(f"✅ Already downloaded: {filename}")
    else:
        print(f"⬇️ Downloading: {filename}")
        response = requests.get(url)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(response.content)
    return filepath, filename


# === MAIN CHUNKING LOGIC ===

def extract_atomic_rules(filepath, source_doc_id):
    with open(filepath, encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    rule_pattern = re.compile(r"^(\d{3})\.(\d+)([a-z]?)\.?\s")
    seen_rules = set()
    chunks = []
    chunk_counter = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        match = rule_pattern.match(line)
        if match:
            rule_root = match.group(1)
            rule_middle = match.group(2)
            rule_suffix = match.group(3)
            rule_number = f"{rule_root}.{rule_middle}{rule_suffix}"
            rule_group = f"{rule_root}.{rule_middle}" if rule_suffix else ""

            if rule_number in seen_rules:
                i += 1
                continue
            seen_rules.add(rule_number)

            base_text = line.strip()
            examples = []

            # Collect any "Example:" lines that follow this rule
            j = i + 1
            while j < len(lines) and lines[j].startswith("Example:"):
                examples.append(lines[j])
                j += 1

            # Build full text with examples included
            full_text = base_text
            if examples:
                full_text += "\n" + "\n".join(examples)

            chunk_data = {
                "chunk_id": f"line-{chunk_counter:05d}",
                "rule_root": rule_root,
                "rule_group": rule_group,
                "rule_number": rule_number,
                "text": full_text,
                "examples": examples,
                "token_count": len(full_text.split()),
                "source_doc": source_doc_id
            }
            chunks.append(chunk_data)
            chunk_counter += 1
            i = j  # Skip past example lines
        else:
            i += 1

    return chunks


def extract_glossary_chunks(filepath, source_doc_id):
    with open(filepath, encoding="utf-8") as f:
        lines = [line.rstrip() for line in f]

    # Find glossary section: from last "Glossary" to first "Credits"
    glossary_start_idx = max(i for i, line in enumerate(lines) if "glossary" in line.lower())
    try:
        glossary_end_idx = next(i for i in range(glossary_start_idx + 1, len(lines)) if "credits" in lines[i].lower())
    except StopIteration:
        glossary_end_idx = len(lines)

    glossary_lines = lines[glossary_start_idx + 1 : glossary_end_idx]

    chunks = []
    chunk_id = 0
    current_term = None
    definition_lines = []

    for line in glossary_lines:
        if not line.strip():  # empty line = end of entry
            if current_term:
                definition = " ".join(definition_lines).strip()
                if definition:
                    chunks.append({
                        "chunk_id": f"glossary-{chunk_id:04d}",
                        "type": "glossary",
                        "term": current_term,
                        "definition": definition,
                        "token_count": len(definition.split()),
                        "source_doc": source_doc_id
                    })
                    chunk_id += 1
                current_term = None
                definition_lines = []
            continue

        if current_term is None:
            current_term = line.strip()
        else:
            definition_lines.append(line.strip())

    # Handle final entry if file ends cleanly
    if current_term and definition_lines:
        definition = " ".join(definition_lines).strip()
        chunks.append({
            "chunk_id": f"glossary-{chunk_id:04d}",
            "type": "glossary",
            "term": current_term,
            "definition": definition,
            "token_count": len(definition.split()),
            "source_doc": source_doc_id
        })

    return chunks


# === MAIN ===

def main():
    try:
        txt_url = get_latest_rules_txt_url()
        filepath, filename = download_file_if_new(txt_url, DOWNLOAD_DIR)
        source_doc_id = filename.replace(".txt", "")
        chunks = extract_atomic_rules(filepath, source_doc_id)

        with open(OUTPUT_RULES_JSON, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        print(f"\n✅ {len(chunks)} atomic rule chunks saved to {OUTPUT_RULES_JSON}")

        chunks = extract_glossary_chunks(filepath, source_doc_id)
        with open(OUTPUT_GLOSSARY_JSON, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        print(f"\n✅ {len(chunks)} glossary chunks saved to {OUTPUT_RULES_JSON}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
