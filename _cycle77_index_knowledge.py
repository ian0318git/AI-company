"""Index knowledge files from disk into the database."""
import os
import json
import uuid
from datetime import datetime, timezone
import sqlite3

KNOWLEDGE_DIR = "src/ai_embedded_company/knowledge"
DB_PATH = "data/ai_embedded_company.db"

def categorize_file(filename):
    """Determine category and board_family from filename and content."""
    name_lower = filename.lower()
    if name_lower.startswith("esp32"):
        return "hardware-spec", "esp32"
    elif name_lower.startswith("m5stack"):
        return "hardware-spec", "m5stack"
    elif name_lower.startswith("research"):
        return "research", None
    elif "cycle" in name_lower:
        return "cycle-report", None
    elif "prompt" in name_lower:
        return "design-doc", None
    elif "multi_agent" in name_lower:
        return "report", None
    else:
        return "general", None

def extract_tags(content, filename):
    """Extract tags from content and filename."""
    tags = set()
    content_lower = content.lower()
    # Board tags
    if "esp32" in content_lower:
        tags.add("esp32")
    if "m5stack" in content_lower:
        tags.add("m5stack")
    if "stm32" in content_lower:
        tags.add("stm32")
    # Topic tags
    if "pipeline" in content_lower:
        tags.add("pipeline")
    if "evolution" in content_lower:
        tags.add("evolution")
    if "prompt" in content_lower:
        tags.add("prompt")
    if "test" in content_lower or "pytest" in content_lower:
        tags.add("testing")
    if "api" in content_lower:
        tags.add("api")
    if "antibody" in content_lower or "vaccine" in content_lower:
        tags.add("evolution")
    # Filename-based tags
    if "cycle" in filename.lower():
        tags.add("cycle-report")
    if "research" in filename.lower():
        tags.add("research")
    return list(tags)

def main():
    print(f"Scanning {KNOWLEDGE_DIR} for knowledge files...")
    files = sorted(os.listdir(KNOWLEDGE_DIR))
    files = [f for f in files if f.endswith((".md", ".json")) and not f.startswith("__")]
    print(f"Found {len(files)} knowledge files on disk")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT COUNT(*) FROM knowledge")
    existing = cur.fetchone()[0]
    print(f"Existing DB entries: {existing}")

    if existing > 0:
        print(f"Re-indexing: clearing {existing} existing entries first.")
        conn.execute("DELETE FROM knowledge")

    indexed = 0
    for filename in files:
        filepath = os.path.join(KNOWLEDGE_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        title = filename.replace(".md", "").replace(".json", "")
        title = title.replace("_", " ").replace("-", " ").title()

        category, board_family = categorize_file(filename)
        tags = extract_tags(content, filename)

        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO knowledge (id, title, content, category, tags, board_family, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), title, content, category, json.dumps(tags), board_family, now),
        )
        indexed += 1
        if indexed % 5 == 0:
            print(f"  Indexed {indexed}/{len(files)}...")

    conn.commit()
    cur = conn.execute("SELECT COUNT(*) FROM knowledge")
    total = cur.fetchone()[0]
    conn.close()

    print(f"\nDone: indexed {indexed} files, total in DB: {total}")
    return {"indexed": indexed, "total": total}

if __name__ == "__main__":
    main()
