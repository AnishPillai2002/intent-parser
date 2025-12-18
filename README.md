# 🧠 SQL Intent Parser & Semantic Classifier

A **robust, scalable SQL intent ingestion and classification system** using **vector embeddings, Qdrant, and FastAPI**.
This project converts natural-language SQL requests into structured **SQL intent representations** with high accuracy and safety.

---

## 🚀 Features

* Semantic SQL intent classification
* Vector-based intent matching using Qdrant
* Idempotent, safe intent ingestion
* Deduplicated and optimized embeddings
* Rich intent metadata for filtering and ranking
* FastAPI-based ingestion and query APIs
* Production-ready logging & observability

---

## 🧩 Architecture Overview

```
┌───────────────┐
│ SQL Intents   │
│ (JSON Dicts)  │
└───────┬───────┘
        │
        ▼
┌────────────────────┐
│ Text Normalization │
│ + Deduplication    │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ Embedding Generator│
│ (batch_embed)      │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ text → vector map  │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ Qdrant Vector Store│
│ (Idempotent IDs)   │
└────────────────────┘
```

---

## 📁 Project Structure

```
app/
├── api/
│   └── ingestion_routes.py      # FastAPI ingestion endpoint
│
├── intents/
│   ├── sql_intents.py           # SQL intent definitions
│   └── ingest.py                # Vector ingestion logic
│
├── embeddings/
│   └── embedder.py               # Embedding generator
│
├── vectorstore/
│   └── qdrant_client.py          # Qdrant connection & setup
│
├── utils/
│   └── idempotent_id.py          # Stable ID generator
│
├── config.py                     # App configuration
└── main.py                       # FastAPI entry point
```

---

## ⚡ Quick Setup

### 1️⃣ Clone the repository

```bash
git clone https://github.com/your-org/sql-intent-parser.git
cd sql-intent-parser
```

---

### 2️⃣ Create virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows
```

---

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Start Qdrant

```bash
docker run -p 6333:6333 qdrant/qdrant
```

---

### 5️⃣ Run FastAPI server

```bash
uvicorn app.main:app --reload
```

---

### 6️⃣ Ingest SQL intents

```bash
curl -X POST http://localhost:8000/api/ingest/intents
```

---

## 📌 SQL Intent Format

Each intent is defined as a structured dictionary:

```python
{
    "id": 101,
    "operation": "SELECT_BASIC",
    "category": "READ",
    "complexity": 1,
    "text": "Retrieve rows from a table without conditions.",
    "examples": [
        "show all users",
        "list all records"
    ],
    "paraphrases": [
        "get everything from the table"
    ],
    "keywords": [
        "select", "fetch", "list"
    ]
}
```

---

## 🧠 How Intent Ingestion Works

### Step 1: Collect all texts

* Description
* Examples
* Paraphrases
* Keywords

---

### Step 2: Deduplicate texts

```python
all_texts = list(set(all_texts))
```

Prevents redundant embedding generation.

---

### Step 3: Batch embedding

```python
vectors = batch_embed(all_texts)
```

Efficient, scalable embedding generation.

---

### Step 4: Safe text → vector mapping

```python
text_vector_map = dict(zip(all_texts, vectors))
```

Eliminates fragile index-based alignment.

---

### Step 5: Idempotent vector storage

```python
id = make_id(intent_id, source, text)
```

Re-ingestion updates existing vectors instead of duplicating.

---

## 🛑 Common Problems & Solutions

### ❌ Problem 1: Fragile Index-Based Alignment

**Issue**

```python
vector = vectors[idx]
idx += 1
```

Breaks on reordering, deduplication, or failures.

✅ **Solution**

```python
vector = text_vector_map[text]
```

---

### ❌ Problem 2: Duplicate Embeddings

**Issue**

* Same keyword embedded hundreds of times

✅ **Solution**

* Global deduplication before embedding

---

### ❌ Problem 3: Non-Idempotent Ingestion

**Issue**

* UUIDs cause duplicates on re-ingestion

✅ **Solution**

* Deterministic IDs using intent metadata

---

### ❌ Problem 4: Poor Debugging Visibility

**Issue**

* No traceability between vectors and intent text

✅ **Solution**

* Store `text`, `source`, and intent metadata in payload

---

## 🧪 Example Stored Vector Payload

```json
{
  "intent_id": 101,
  "operation": "SELECT_BASIC",
  "category": "READ",
  "complexity": 1,
  "source": "example",
  "text": "show all users"
}
```

---

## 📊 Logging & Observability

Sample logs:

```
[INFO] Collected 42 texts for embedding
[INFO] Embedding dimension: 768
[INFO] Stored intent_id=101 with 6 vectors
[INFO] Total vectors stored: 42
```

---

## 🔐 Safety & Scalability Guarantees

| Concern         | Handled             |
| --------------- | ------------------- |
| Re-ingestion    | ✅ Idempotent        |
| Data corruption | ✅ Prevented         |
| Scaling         | ✅ Batch + Dedup     |
| Debugging       | ✅ Full traceability |
| Production use  | ✅ Ready             |

---

## 📈 Future Enhancements

* Hybrid rule + vector classifier
* Confidence-weighted intent scoring
* Schema-aware intent validation
* Query rewrite safety layer
* Multi-DB support (Postgres, MySQL, Snowflake)

---

## 🧠 Who Should Use This?

* NL → SQL systems
* AI database assistants
* Query understanding engines
* Semantic SQL tooling
* Enterprise analytics platforms

---

## 📜 License

MIT License

---

## 🙌 Final Note

This project is designed with **production reliability in mind**, not just demo-level functionality.
Every architectural choice prioritizes **correctness, scalability, and debuggability**.

---
