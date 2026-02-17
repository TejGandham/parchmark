# AI Embeddings — Design Document

> Phase 2 of the Command Palette redesign. Adds content-based similarity scoring to the "For You" section using OpenAI embeddings.

<!-- machine-readable revision block — do not edit manually -->
<!-- revision: 1.0.0 -->
<!-- date: 2026-02-16 -->
<!-- commit: 45300c8 -->
<!-- pr: #26 -->
<!-- status: merged -->

| | |
|---|---|
| **Revision** | `1.0.0` |
| **Date** | 2026-02-16 |
| **Author** | AI Embeddings team |
| **Status** | **Merged** → main |
| **PR** | [#26](https://brahma.myth-gecko.ts.net:3000/stackhouse/parchmark/pulls/26) `feature/ai-embeddings` |
| **Commit** | [`45300c8`](https://brahma.myth-gecko.ts.net:3000/stackhouse/parchmark/commit/45300c8) |
| **Merge** | [`8a679b3`](https://brahma.myth-gecko.ts.net:3000/stackhouse/parchmark/commit/8a679b3) |
| **Depends on** | Phase 1 — Command Palette (#25) |

### Revision History

| Rev | Date | Commit | Description |
|-----|------|--------|-------------|
| `1.0.0` | 2026-02-16 | `45300c8` | Initial release — embeddings service, similarity endpoint, blended scoring, backfill CLI |

## System Overview

```mermaid
graph LR
    subgraph Frontend
        CP[Command Palette]
        SC[Scoring Engine]
        API_CLIENT[API Client]
    end

    subgraph Backend
        ROUTER[Notes Router]
        EMB_SVC[Embeddings Service]
        SIM_EP[Similarity Endpoint]
    end

    subgraph External
        OPENAI[OpenAI API<br/>text-embedding-3-small]
    end

    subgraph Storage
        PG[(PostgreSQL<br/>notes.embedding JSON)]
    end

    CP -->|palette opens| API_CLIENT
    API_CLIENT -->|GET /notes/:id/similar| SIM_EP
    SIM_EP -->|load embeddings| PG
    SIM_EP -->|cosine similarity| EMB_SVC
    SIM_EP -->|top N results| API_CLIENT
    API_CLIENT -->|SimilarNote[]| SC
    SC -->|blended scores| CP

    ROUTER -->|create/update note| EMB_SVC
    EMB_SVC -->|generate embedding| OPENAI
    EMB_SVC -->|store vector| PG
```

## Scoring Pipeline

```mermaid
flowchart TD
    OPEN[User opens<br/>Command Palette] --> HAS_NOTE{Viewing a<br/>note?}
    HAS_NOTE -->|No| HEURISTIC_ONLY[Heuristic-only scoring<br/>60% recency + 40% frequency]
    HAS_NOTE -->|Yes| FETCH[GET /notes/:id/similar]
    FETCH --> GOT_RESULTS{Got similar<br/>notes?}
    GOT_RESULTS -->|Empty or error| HEURISTIC_ONLY
    GOT_RESULTS -->|SimilarNote array| BLEND

    subgraph BLEND [Blended Scoring]
        direction TB
        H[Heuristic Score<br/>per candidate note]
        S[Similarity Score<br/>from API response]
        F["Final = 0.4 × heuristic + 0.6 × similarity"]
        H --> F
        S --> F
    end

    BLEND --> RANK[Sort by final score<br/>Return top 3]
    HEURISTIC_ONLY --> RANK
    RANK --> DISPLAY[Render For You section]

    style BLEND fill:#f0f4ff,stroke:#4a6cf7
    style HEURISTIC_ONLY fill:#fff8e6,stroke:#e6a817
    style DISPLAY fill:#e8f5e9,stroke:#43a047
```

## Embedding Lifecycle

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant API as FastAPI
    participant SVC as Embeddings Service
    participant OAI as OpenAI API
    participant DB as PostgreSQL

    Note over U,DB: Note Creation / Update

    U->>FE: Save note content
    FE->>API: POST /notes (or PUT /notes/:id)
    API->>DB: INSERT/UPDATE note row
    DB-->>API: ✓ saved
    API->>SVC: generate_embedding(content)
    SVC->>OAI: embeddings.create(text[:32000])
    alt API key set & success
        OAI-->>SVC: float[1536]
        SVC-->>API: embedding vector
        API->>DB: UPDATE notes SET embedding = [...]
    else No API key or failure
        OAI-->>SVC: error / None
        SVC-->>API: None
        Note right of API: Note saved without<br/>embedding. No error.
    end
    API-->>FE: NoteResponse

    Note over U,DB: Similarity Query

    U->>FE: Open Command Palette
    FE->>API: GET /notes/:id/similar?count=5
    API->>DB: SELECT embedding FROM notes WHERE id = :id
    API->>DB: SELECT id, embedding FROM notes<br/>WHERE user_id = :uid AND embedding IS NOT NULL
    API->>SVC: compute_similarity(target, each)
    SVC-->>API: cosine scores
    API-->>FE: [{id, title, similarity, updatedAt}]
    FE->>FE: getBlendedForYouNotes()
```

## Data Model

```mermaid
erDiagram
    USERS ||--o{ NOTES : owns
    USERS {
        int id PK
        string username UK
        string password_hash
        string auth_provider
        datetime created_at
    }
    NOTES {
        string id PK "note-{timestamp}"
        int user_id FK
        string title
        text content
        json embedding "float[1536] or NULL"
        int access_count "default 0"
        datetime last_accessed_at
        datetime created_at
        datetime updated_at
    }
```

## Migration Chain

```mermaid
graph LR
    M1["170dd30cebde<br/>initial"] --> M2["fad201191d3b<br/>access tracking"]
    M2 --> M3["33a4da6b0cac<br/>add embedding JSON"]
    style M3 fill:#e8f5e9,stroke:#43a047
```

The migration is idempotent — checks if the column exists before adding it.

## Graceful Degradation

```mermaid
flowchart TD
    START([System Start]) --> KEY_CHECK{OPENAI_API_KEY<br/>set?}

    KEY_CHECK -->|No| NO_EMB[Embeddings disabled]
    KEY_CHECK -->|Yes| EMB_ON[Embeddings enabled]

    NO_EMB --> SAVE_NOEMB[Notes save normally<br/>embedding = NULL]
    NO_EMB --> SIM_NOEMB[GET /similar returns []]
    NO_EMB --> SCORE_HEUR[Command Palette uses<br/>heuristic-only scoring]

    EMB_ON --> SAVE_EMB[Notes save +<br/>embedding generated]
    EMB_ON --> API_FAIL{OpenAI call<br/>fails?}
    API_FAIL -->|Yes| SAVE_NOEMB
    API_FAIL -->|No| SAVE_OK[Note saved with<br/>embedding vector]

    SAVE_OK --> SIM_OK[GET /similar returns<br/>ranked results]
    SIM_OK --> SCORE_BLEND[Command Palette uses<br/>blended scoring]

    style NO_EMB fill:#fff8e6,stroke:#e6a817
    style EMB_ON fill:#e8f5e9,stroke:#43a047
    style API_FAIL fill:#fce4ec,stroke:#e53935
```

Every path leads to a working app. No feature flags needed.

## Component Architecture

```mermaid
graph TB
    subgraph "Frontend (React)"
        CP["CommandPalette.tsx"]
        BLEND_FN["getBlendedForYouNotes()"]
        HEUR_FN["computeForYouScore()"]
        API_FN["getSimilarNotes()"]
        REQ["request() → fetch"]

        CP -->|"useMemo"| BLEND_FN
        BLEND_FN --> HEUR_FN
        CP -->|"useEffect on open"| API_FN
        API_FN --> REQ
    end

    subgraph "Backend (FastAPI)"
        NR["notes.py router"]
        CREATE["POST / — create_note"]
        UPDATE["PUT /:id — update_note"]
        SIMILAR["GET /:id/similar"]
        GEN["generate_embedding()"]
        COMP["compute_similarity()"]

        NR --- CREATE
        NR --- UPDATE
        NR --- SIMILAR
        CREATE -->|"fire-and-forget"| GEN
        UPDATE -->|"fire-and-forget"| GEN
        SIMILAR --> COMP
    end

    subgraph "Backfill CLI"
        BF["python -m app.services.backfill"]
        BF -->|"rate-limited loop"| GEN
    end

    REQ -->|"HTTP"| SIMILAR

    style CP fill:#dbeafe,stroke:#3b82f6
    style BLEND_FN fill:#dbeafe,stroke:#3b82f6
    style SIMILAR fill:#fef3c7,stroke:#f59e0b
    style GEN fill:#fce7f3,stroke:#ec4899
    style BF fill:#f3e8ff,stroke:#a855f7
```

## API Contract

```mermaid
graph LR
    subgraph Request
        R["GET /api/notes/{noteId}/similar?count=5"]
    end

    subgraph Response["Response — SimilarNoteResponse[]"]
        direction TB
        R1["{ id, title, similarity: 0.92, updatedAt }"]
        R2["{ id, title, similarity: 0.85, updatedAt }"]
        R3["{ id, title, similarity: 0.71, updatedAt }"]
    end

    Request --> Response

    style Request fill:#eff6ff,stroke:#3b82f6
    style Response fill:#f0fdf4,stroke:#22c55e
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Note ID |
| `title` | `string` | Note title |
| `similarity` | `float` | Cosine similarity `[0, 1]`, rounded to 4 decimals |
| `updatedAt` | `string` | ISO 8601 timestamp |

## Cosine Similarity

```mermaid
graph LR
    A["Note A<br/>embedding ∈ ℝ¹⁵³⁶"] --- COS["cos(A, B) = A·B / (‖A‖ × ‖B‖)"]
    B["Note B<br/>embedding ∈ ℝ¹⁵³⁶"] --- COS
    COS --> CLAMP["clamp(0, 1)"]
    CLAMP --> SCORE["similarity score"]

    style COS fill:#fef3c7,stroke:#f59e0b
```

Computed in Python — no pgvector needed. For ~200 notes, full pairwise comparison takes **< 10ms**.

## Backfill Process

```mermaid
flowchart TD
    START([Run backfill CLI]) --> CHECK_KEY{OPENAI_API_KEY?}
    CHECK_KEY -->|Missing| EXIT_ERR[Exit code 1]
    CHECK_KEY -->|Present| QUERY["SELECT notes WHERE<br/>embedding IS NULL"]
    QUERY --> COUNT{Notes found?}
    COUNT -->|0| EXIT_OK_NOOP["All notes embedded.<br/>Exit code 0"]
    COUNT -->|N > 0| LOOP

    subgraph LOOP ["Process each note"]
        direction TB
        GEN["generate_embedding(content)"]
        SAVE["UPDATE notes SET embedding = [...]"]
        WAIT["sleep(0.5s) rate limit"]
        GEN --> SAVE --> WAIT
    end

    LOOP --> RESULT["Log: N succeeded, M failed"]
    RESULT --> EXIT_CODE{Any failures?}
    EXIT_CODE -->|Yes| EXIT_1[Exit code 1]
    EXIT_CODE -->|No| EXIT_0[Exit code 0]

    style LOOP fill:#f5f3ff,stroke:#8b5cf6
    style EXIT_ERR fill:#fce4ec,stroke:#e53935
```

```bash
# Usage
cd backend
OPENAI_API_KEY=sk-... uv run python -m app.services.backfill
```

## Configuration

```mermaid
graph TB
    subgraph "Environment Variables"
        KEY["OPENAI_API_KEY<br/><i>optional — enables embeddings</i>"]
        MODEL["EMBEDDING_MODEL<br/><i>default: text-embedding-3-small</i>"]
    end

    subgraph "Hardcoded"
        DIM["EMBEDDING_DIMENSIONS = 1536"]
        RATE["RATE_LIMIT_SECONDS = 0.5"]
        TRUNC["TEXT_TRUNCATION = 32,000 chars"]
        HEUR_W["Heuristic weight = 0.4"]
        SIM_W["Similarity weight = 0.6"]
    end

    style KEY fill:#fef3c7,stroke:#f59e0b
    style MODEL fill:#fef3c7,stroke:#f59e0b
```

## File Map

```mermaid
graph TB
    subgraph "Backend — New Files"
        E["app/services/embeddings.py<br/><i>OpenAI client + cosine similarity</i>"]
        BF["app/services/backfill.py<br/><i>CLI backfill command</i>"]
        MIG["migrations/.../33a4da6b0cac<br/><i>Add embedding JSON column</i>"]
    end

    subgraph "Backend — Modified"
        MOD["app/models/models.py<br/><i>+ embedding column</i>"]
        RTR["app/routers/notes.py<br/><i>+ hooks + GET /similar</i>"]
        SCH["app/schemas/schemas.py<br/><i>+ SimilarNoteResponse</i>"]
    end

    subgraph "Frontend — Modified"
        API_CFG["config/api.ts<br/><i>+ NOTES.SIMILAR</i>"]
        TYPES["types/index.ts<br/><i>+ SimilarNote</i>"]
        API_SVC["services/api.ts<br/><i>+ getSimilarNotes()</i>"]
        SCORE["utils/noteScoring.ts<br/><i>+ getBlendedForYouNotes()</i>"]
        CMPAL["CommandPalette.tsx<br/><i>fetch + blend on open</i>"]
    end

    RTR --> E
    RTR --> SCH
    BF --> E
    CMPAL --> SCORE
    CMPAL --> API_SVC
    API_SVC --> API_CFG

    style E fill:#fce7f3,stroke:#ec4899
    style BF fill:#f3e8ff,stroke:#a855f7
    style MIG fill:#e8f5e9,stroke:#43a047
```

## Test Coverage

```mermaid
pie title New Tests Added (35 total)
    "Embeddings unit" : 10
    "Similarity integration" : 9
    "Backfill unit" : 6
    "Scoring unit" : 6
    "CommandPalette" : 4
```

| Suite | Tests | Covers |
|-------|-------|--------|
| `test_embeddings.py` | 10 | Client init, generation, cosine similarity edge cases |
| `test_similarity.py` | 9 | Endpoint auth, 404, no-embedding, ranking, count param |
| `test_backfill.py` | 6 | No-key exit, no-work skip, rate limiting, failure reporting |
| `noteScoring.test.ts` | 6 | Blend fallback, empty similarity, weight verification |
| `CommandPalette.test.tsx` | 4 | Fetch on open, no-fetch without note, error resilience |

## Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| **Storage** | JSON column (not pgvector) | ~200 notes/user → Python cosine similarity < 10ms. Avoids pgvector Docker/deployment complexity. |
| **Timing** | Synchronous on save | Note saves are infrequent. 200-500ms OpenAI latency is acceptable. No Celery/Redis needed. |
| **Failure mode** | Fire-and-forget | Embedding failure never blocks note saves. Logs warning, moves on. |
| **Model** | `text-embedding-3-small` | Best cost/quality ratio. 1536 dimensions. Configurable via env var. |
| **Blend weights** | 40% heuristic / 60% similarity | AI signal is stronger, but recency/frequency prevents stale recommendations. |
| **Truncation** | 32,000 chars | OpenAI's token limit for embedding input. Covers virtually all notes. |
