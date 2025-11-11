# Summary Service Architecture

## Overview

The Summary Service is a Django-based microservice that generates stakeholder-specific summaries from construction project documents using LangChain and OpenAI's GPT models.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Summary Service                           │
│                                                                   │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │   Django     │      │  LangChain   │      │   OpenAI     │  │
│  │   REST API   │─────▶│  Orchestrator│─────▶│   GPT-4      │  │
│  └──────────────┘      └──────────────┘      └──────────────┘  │
│         │                      │                                 │
│         │                      │                                 │
│         ▼                      ▼                                 │
│  ┌──────────────────────────────────┐                           │
│  │        PostgreSQL Database       │                           │
│  │  - SummaryJob                    │                           │
│  │  - GeneratedSummary              │                           │
│  │  - SummarySection                │                           │
│  │  - DocumentContext               │                           │
│  └──────────────────────────────────┘                           │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
         ▲                                    │
         │                                    │
         │ HTTP                               │ HTTP
         │                                    ▼
┌────────┴─────────┐              ┌──────────────────┐
│   API Clients    │              │  Other Services  │
│  - Web App       │              │  - Ingestion     │
│  - Mobile App    │              │  - Extraction    │
└──────────────────┘              └──────────────────┘
```

## Components

### 1. Django REST API (views.py)

**Purpose:** Exposes HTTP endpoints for summary generation and retrieval.

**Key Endpoints:**
- `POST /api/summaries/generate/` - Generate new summary
- `GET /api/summaries/{id}/` - Get job details
- `GET /api/summaries/{id}/result/` - Get generated summary
- `GET /api/summaries/by_project/{project_id}/` - List project summaries

**Features:**
- Request validation using DRF serializers
- Pagination and filtering
- Error handling
- Status polling for async operations

### 2. LangChain Orchestrator (services.py)

**Purpose:** Orchestrates LLM interactions for summary generation.

**Key Components:**

#### SummaryGenerationService
Main service class that:
- Manages LLM configuration
- Handles prompt engineering
- Implements map-reduce for large documents
- Tracks token usage
- Generates structured output

**Workflow:**
```
1. Fetch document contexts
2. Combine/chunk documents
3. Generate stakeholder-specific prompts
4. Call LLM via LangChain
5. Parse and structure response
6. Save to database
```

**Strategies:**
- **Single Document**: Direct LLM call for small inputs
- **Multi-Document**: Map-reduce approach for large inputs
  1. Summarize each chunk
  2. Combine chunk summaries
  3. Generate final summary

### 3. Data Models (models.py)

#### SummaryJob
Tracks summary generation requests.

**Fields:**
- `id`: Unique job identifier
- `project_id`: Associated project
- `stakeholder_role`: Target audience
- `document_ids`: Source documents
- `focus_areas`: Specific topics
- `status`: pending/processing/completed/failed
- `model_used`: LLM model identifier
- `tokens_used`: Token consumption
- `processing_time`: Duration in seconds

#### GeneratedSummary
Stores completed summaries.

**Fields:**
- `id`: Summary identifier
- `job`: Foreign key to SummaryJob
- `full_summary`: Complete summary text
- `sections`: Related SummarySection objects

#### SummarySection
Individual summary sections.

**Fields:**
- `summary`: Foreign key to GeneratedSummary
- `title`: Section heading
- `content`: Section body
- `key_points`: List of highlights
- `evidence_ids`: Supporting document IDs
- `order`: Display sequence

#### DocumentContext
Links documents to summary jobs.

**Fields:**
- `job`: Foreign key to SummaryJob
- `document_id`: Document identifier
- `extracted_text`: Relevant content
- `relevance_score`: 0-1 score
- `metadata`: Additional information

### 4. Database (PostgreSQL)

**Schema:**
```sql
summary_jobs
├── id (PK)
├── project_id (indexed)
├── stakeholder_role (indexed)
├── document_ids (array)
├── focus_areas (array)
├── status (indexed)
├── model_used
├── tokens_used
├── processing_time
└── timestamps

generated_summaries
├── id (PK)
├── job_id (FK, unique)
├── project_id (indexed)
├── stakeholder_role (indexed)
├── full_summary (text)
└── timestamps

summary_sections
├── id (PK)
├── summary_id (FK, indexed)
├── title
├── content (text)
├── order
├── key_points (array)
└── evidence_ids (array)

document_contexts
├── id (PK)
├── job_id (FK, indexed)
├── document_id (indexed)
├── extracted_text (text)
├── relevance_score
└── metadata (jsonb)
```

## Data Flow

### Summary Generation Flow

```
1. Client Request
   POST /api/summaries/generate/
   {
     document_ids: [...],
     project_id: "...",
     stakeholder_role: "developer",
     focus_areas: [...]
   }
   │
   ▼
2. Create SummaryJob
   - Validate input
   - Generate job ID
   - Set status = "pending"
   - Save to database
   │
   ▼
3. Fetch Document Contexts
   - Query ingestion service for documents
   - Extract relevant text
   - Calculate relevance scores
   - Create DocumentContext records
   │
   ▼
4. Prepare LangChain Pipeline
   - Select stakeholder prompt template
   - Split large documents if needed
   - Configure LLM parameters
   │
   ▼
5. Generate Summary
   - Set status = "processing"
   - Execute LangChain chain
   - Track token usage
   - Parse structured output
   │
   ▼
6. Save Results
   - Create GeneratedSummary
   - Create SummarySection records
   - Set status = "completed"
   - Record metadata (tokens, time)
   │
   ▼
7. Return Response
   {
     job_id: "...",
     status: "completed",
     summary: {...}
   }
```

## Stakeholder Customization

Each stakeholder role receives tailored summaries:

### Developer
- **Focus:** Technical specs, codes, quality
- **Sections:** Technical Overview, Quality Standards, Compliance, Risks

### Contractor
- **Focus:** Scope, timelines, resources
- **Sections:** Project Scope, Timeline, Resources, Change Management

### Architect
- **Focus:** Design, specifications, codes
- **Sections:** Design Overview, Specifications, Code Compliance, Changes

### Client
- **Focus:** Progress, budget, quality
- **Sections:** Project Status, Budget Summary, Timeline, Quality

### Project Manager
- **Focus:** Status, risks, resources
- **Sections:** Executive Summary, Risk & Issues, Resources, Decisions

### Legal
- **Focus:** Contracts, compliance, claims
- **Sections:** Contractual Overview, Compliance, Claims & Disputes, Risks

### Finance
- **Focus:** Costs, budget, payments
- **Sections:** Financial Summary, Budget Variance, Cash Flow, Risks

### Executive
- **Focus:** Strategy, risks, decisions
- **Sections:** Executive Summary, Strategic Overview, Financial Health, Actions

## LangChain Integration

### Prompt Engineering

**System Prompt:**
```
You are an expert construction project analyst specializing in
stakeholder-specific summaries. Analyze documents and create
concise, actionable summaries tailored to {stakeholder_role}.

Focus on: {focus_areas}
Length: {max_length} words
```

**Human Prompt:**
```
Documents:
{document_content}

Generate a summary with sections:
{section_titles}

For each section:
1. Clear, actionable content
2. 2-4 key points
3. Document references
```

### Token Management

- **Context Window:** 32,000 tokens (GPT-4 Turbo)
- **Chunking:** 4,000 tokens per chunk with 200 overlap
- **Estimation:** ~4 characters per token
- **Tracking:** Use OpenAI callback for accurate counts

### Error Handling

- **Rate Limits:** Exponential backoff with retry
- **Token Limits:** Automatic chunking and map-reduce
- **Model Errors:** Fallback to base model
- **Parse Errors:** Fallback parsing strategy

## Performance Considerations

### Optimization Strategies

1. **Document Filtering:**
   - Calculate relevance scores
   - Only include relevant documents
   - Limit to 50 documents max

2. **Caching:**
   - Cache generated summaries
   - Cache document contexts
   - TTL: 1 hour (configurable)

3. **Async Processing:**
   - Use Celery for background jobs
   - Implement job queues
   - Status polling instead of blocking

4. **Batching:**
   - Batch multiple summary requests
   - Reduce API calls to OpenAI
   - Optimize database queries

### Scalability

- **Horizontal Scaling:** Stateless API servers
- **Database:** Read replicas for queries
- **Caching:** Redis for session/result caching
- **Queue:** Celery with Redis/RabbitMQ
- **Monitoring:** Track token usage, latency, errors

## Security

- **API Keys:** Store securely in environment variables
- **Input Validation:** Strict DRF serializers
- **SQL Injection:** Use Django ORM
- **Rate Limiting:** Prevent abuse
- **Authentication:** Token-based auth (to be implemented)
- **Authorization:** Role-based access control

## Monitoring & Observability

### Metrics to Track

- Request rate and latency
- Token usage and costs
- Error rates by type
- Summary generation time
- Model performance (accuracy)

### Logging

- Request/response logging
- LangChain tracing (LangSmith)
- Error tracking with stack traces
- Performance profiling

## Future Enhancements

1. **Fine-Tuning:** Train custom models on construction data
2. **RAG:** Implement retrieval-augmented generation
3. **Streaming:** Stream responses for real-time UX
4. **Multi-Modal:** Include images/diagrams in summaries
5. **Feedback Loop:** Learn from user ratings
6. **Templates:** Allow custom summary templates
7. **Webhooks:** Notify on completion
8. **Versions:** Track summary versions
9. **Comparison:** Compare summaries across time
10. **Export:** PDF/Word export options

## Dependencies

- **Django:** Web framework
- **DRF:** API framework
- **LangChain:** LLM orchestration
- **OpenAI:** LLM provider
- **PostgreSQL:** Data storage
- **Celery:** Async tasks (future)
- **Redis:** Caching (future)
