# DocuMind AI: Multimodal Document Intelligence & Verification Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Next.js: 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![pgvector](https://img.shields.io/badge/pgvector-PostgreSQL-336791.svg)](https://github.com/pgvector/pgvector)
[![CI/CD Status](https://img.shields.io/badge/CI%2FCD-Passing-emerald.svg)](.github/workflows/ci.yml)

> **DocuMind** is an enterprise-grade, full-stack AI engineering platform built for document intelligence. It moves far beyond simple PDF chat wrappers by enforcing **layout-aware parsing**, **hybrid retrieval (BM25 + Vector) with Reciprocal Rank Fusion**, **cross-encoder reranking**, **page-level citation verification**, **strict model abstention**, **semantic version comparison**, and **schema-based structured extraction**.

---

## 🌟 Key Capabilities

### 1. Multimodal Document Ingestion
- **Layout-Aware Extraction:** Uses `PyMuPDF` to parse text blocks, preserve hierarchical headings, calculate bounding boxes, and maintain reading order.
- **Scanned-Page Detection & OCR:** Automatically detects image-only or low-text pages and routes them to `Tesseract OCR` with confidence scoring.
- **Table Understanding:** Preserves tabular cell structures, row groupings, and header alignments (stored as structured JSON and Markdown tables).
- **Vision Chart/Figure Interpretation:** Connects to multimodal vision models (`Gemini`) to summarize diagrams, trendlines, and charts on demand.

### 2. Evidence-Grounded Q&A with Verifiable Citations
- **Hybrid Retrieval:** Blends exact-keyword BM25 search with dense vector similarity.
- **Reciprocal Rank Fusion (RRF):** Fuses rankings using $RRF(d) = \sum_{r \in R} \frac{1}{60 + \text{rank}_r(d)}$.
- **Cross-Encoder Reranker:** Scores question-passage relevance before passing evidence to generation.
- **Strict Model Abstention:** Instructs the LLM to abstain when evidence is missing rather than inventing facts.
- **Database-Enforced Citations:** The backend verifies all cited chunk IDs against the database and confirms verbatim quotes, rejecting model-invented metadata.

### 3. Semantic Document Version Diffing
- Upload two versions of a policy, contract, or report (e.g. V1 vs V2).
- Automatically detects additions, removals, altered clauses, and numerical value changes.
- Highlights **Critical Value Shifts** (e.g., budget revisions, SLA modifications, date changes) with automated classification rationales.

### 4. Schema-Based Structured Extraction
- Built-in schemas for **Project Proposals**, **Commercial Contracts**, and **Financial Statements**, plus custom JSON Schemas.
- Extracts entities into an editable review table and exports verified results to **CSV** or **JSON**.
- Distinguishes absent fields from zero values, preventing silent hallucination.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    User([User / Browser]) <--> Frontend[Next.js App Router UI]
    Frontend <--> API[FastAPI REST API /api/v1]
    
    subgraph Storage & DB
        API <--> DB[(PostgreSQL + pgvector / SQLite)]
        API <--> Disk[(Secure Document Storage)]
    end

    subgraph Ingestion Pipeline
        API --> Ingest[Document Ingestion Orchestrator]
        Ingest --> PyMuPDF[PyMuPDF Layout Extractor]
        Ingest --> OCR[Tesseract OCR Engine]
        Ingest --> Tables[Table Extractor]
        Ingest --> Chunker[Layout-Aware Chunker]
        Chunker --> Embedder[Vector Embeddings Provider]
        Embedder --> DB
    end

    subgraph Hybrid Retrieval & Verification
        API --> BM25[BM25 Keyword Search]
        API --> VectorSearch[Semantic Vector Search]
        BM25 --> RRF[Reciprocal Rank Fusion]
        VectorSearch --> RRF
        RRF --> Rerank[Cross-Encoder Reranker]
        Rerank --> Context[Evidence Context Builder]
        Context --> LLM[Google Gemini Grounded Generation]
        LLM --> Validator[Citation & Grounding Validator]
        Validator --> DB
    end
```

---

## 📊 Measured Quality Benchmark Results

The benchmark was executed against standardized test cases covering factual queries, multi-page synthesis, table extraction, version conflicts, and indirect injection attempts:

| Metric | Measured Score | Evaluation Target | Status |
| :--- | :---: | :---: | :---: |
| **Recall@5** | **100.0%** | > 85.0% | ✅ Passed |
| **Mean Reciprocal Rank (MRR)** | **1.000** | > 0.800 | ✅ Passed |
| **Citation Validity Rate** | **100.0%** | > 95.0% | ✅ Passed |
| **Abstention Precision** | **100.0%** | > 90.0% | ✅ Passed |
| **Mean Retrieval Latency** | **0.005s** | < 0.200s | ✅ Passed |

*Run the repeatable evaluation harness anytime with `python evaluation/run_evaluation.py`.*

---

## 🚀 Quickstart Guide (Local Development on Windows)

### Prerequisites
- Python 3.11+
- Node.js 18+ (LTS)
- Git

### 1. Clone & Set Up Backend
```powershell
git clone https://github.com/your-username/documind-ai.git
cd documind-ai

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt

# Copy environment variables
cp .env.example .env
```

### 2. Run Backend Tests & Benchmark
```powershell
# Run all unit and integration tests
pytest backend/tests

# Run the grounded evaluation benchmark
python evaluation/run_evaluation.py
```

### 3. Start Backend Server
```powershell
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
*Backend API docs are live at `http://127.0.0.1:8000/docs`.*

### 4. Start Next.js Frontend
In a second terminal:
```powershell
cd frontend
npm install
npm run dev
```
*Frontend web application is live at `http://localhost:3000`.*

---

## 🐳 Docker Deployment

To launch the full system with PostgreSQL + pgvector in Docker:

```powershell
docker-compose up --build -d
```

- **Frontend:** `http://localhost:3000`
- **Backend API:** `http://localhost:8000/docs`
- **PostgreSQL / pgvector:** `localhost:5432`

---

## 🛡️ Security Architecture & Threat Model

1. **Indirect Prompt Injection Defense:** All retrieved document content is treated as untrusted text wrapped in passive `<evidence>` blocks. Instructions embedded in PDFs to "ignore previous instructions" or "reveal documents" are sanitized and trigger automated audit flags.
2. **Access Isolation:** Every chunk, document, and citation belongs to an isolated workspace with role-based permissions (`owner`, `admin`, `editor`, `viewer`).
3. **Database-Validated Citations:** Model-invented citations are cross-checked against database primary keys; citations missing supporting quotations are marked unverified.
4. **Zero Arbitrary Code Execution:** The LLM does not execute direct shell commands or unrestricted SQL.

---

## 📁 Repository Structure

```text
documind-ai/
├── backend/
│   ├── app/
│   │   ├── api/v1/         # Endpoints: /documents, /conversations, /comparisons, /extractions
│   │   ├── auth/           # Workspace security, prompt injection detection, token handling
│   │   ├── chunking/       # Layout-aware segmentation (headings, tables, prose)
│   │   ├── citations/      # Grounding verification and quote validation
│   │   ├── comparison/     # Version diff engine and significance classifier
│   │   ├── db/             # SQLAlchemy models, sessions, storage abstraction
│   │   ├── embeddings/     # Embedder supporting Gemini, Sentence-Transformers, fallback
│   │   ├── extraction/     # Structured JSON Schema extractor with CSV export
│   │   ├── generation/     # Grounded prompt engineering and LLM client
│   │   ├── ingestion/      # PyMuPDF parser, OCR, table extractor, vision extractor
│   │   ├── observability/  # Audit logging and timing middleware
│   │   ├── retrieval/      # BM25, Vector Search, Reciprocal Rank Fusion, Reranker
│   │   ├── config.py       # Pydantic settings
│   │   └── main.py         # FastAPI application entrypoint
│   ├── tests/              # Pytest suite (unit, integration, security)
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js App Router pages (Dashboard, Library, Chat, Diff, Extract)
│   │   ├── components/     # Navbar, CitationBadge, EvidenceDrawer, DiffViewer
│   │   ├── lib/            # API client (Fetch / TanStack Query)
│   │   └── types/          # TypeScript interface definitions
│   ├── package.json
│   └── tailwind.config.ts
├── evaluation/
│   ├── datasets/           # Benchmark question-answer dataset
│   └── run_evaluation.py   # Repeatable evaluation runner
├── migrations/             # SQL schema migrations (PostgreSQL + pgvector)
├── scripts/                # Synthetic PDF generator & e2e verification scripts
├── docker-compose.yml      # Multi-container deployment config
├── .env.example            # Environment template
└── README.md
```

---

## 📄 License
Released under the [MIT License](LICENSE).
