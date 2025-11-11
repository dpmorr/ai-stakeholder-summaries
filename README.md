# Summary Generation Service

LangChain-based summary generation service that creates stakeholder-specific summaries from any type of document.

## Features

- **Stakeholder-Specific Summaries**: Tailored summaries for different roles (technical teams, vendors, clients, executives, etc.)
- **LangChain Orchestration**: Uses LangChain for advanced LLM workflows
- **Fine-Tuned Model Support**: Can use OpenAI fine-tuned models when available
- **Multi-Document Synthesis**: Handles large document sets with map-reduce approach
- **Evidence Linking**: Links summary sections to source documents
- **Structured Output**: Organizes summaries into logical sections with key points
- **PostgreSQL Storage**: Persistent storage of summaries and jobs

## Architecture

```
summary/
├── config/          # Django configuration
├── summary/         # Main app
│   ├── models.py    # SummaryJob, GeneratedSummary, SummarySection, DocumentContext
│   ├── views.py     # DRF ViewSet for API
│   ├── serializers.py  # DRF serializers
│   ├── services.py  # LangChain-based generation logic
│   ├── urls.py      # URL routing
│   └── admin.py     # Django admin
└── manage.py
```

## API Endpoints

### Generate Summary
```bash
POST /api/summaries/generate/
{
  "document_ids": ["doc1", "doc2"],
  "project_id": "project123",
  "stakeholder_role": "executive",
  "focus_areas": ["key_findings", "recommendations"],
  "max_length": 500
}
```

### Get Summary Job
```bash
GET /api/summaries/{job_id}/
```

### Get Summary Result
```bash
GET /api/summaries/{job_id}/result/
```

### List Summaries by Project
```bash
GET /api/summaries/by_project/{project_id}/
```

### List Summaries by Role
```bash
GET /api/summaries/by_role/{role}/
```

## Stakeholder Roles

Each role receives a customized summary:

- **Developer**: Technical specifications, implementation details, system architecture, code quality standards
- **External Partner/Vendor**: Scope of work, deliverables, timelines, resource requirements, dependencies
- **Technical Specialist**: Detailed design specifications, technical requirements, standards compliance, technical changes
- **Client**: Progress updates, budget status, timeline, quality metrics, outcomes
- **Project Manager**: Overall status, risks, issues, resource allocation, milestone tracking
- **Legal**: Contractual obligations, compliance requirements, legal risks, regulatory matters
- **Finance**: Cost analysis, budget variance, payment status, financial forecasts, ROI metrics
- **Executive**: High-level overview, strategic implications, key risks, financial health, decision points

## Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- OpenAI API key

### Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create superuser:
```bash
python manage.py createsuperuser
```

6. Run server:
```bash
python manage.py runserver 8002
```

## Configuration

### OpenAI Models

Set in `.env`:
```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_FINE_TUNED_MODEL=ft:gpt-4-...  # Optional
```

### LangChain Tracing

Enable LangSmith tracing for debugging:
```
LANGCHAIN_TRACING=True
LANGCHAIN_PROJECT=summary-service
LANGCHAIN_API_KEY=ls__...
```

## Database Models

### SummaryJob
Tracks summary generation jobs with status, parameters, and metadata.

### GeneratedSummary
Stores the complete generated summary for a job.

### SummarySection
Individual sections within a summary (e.g., "Executive Summary", "Risk Analysis").

### DocumentContext
Links documents to summary jobs with extracted context.

## LangChain Integration

The service uses LangChain for:
- **Prompt Templates**: Stakeholder-specific prompts
- **Text Splitting**: Handles large documents
- **Map-Reduce**: Synthesizes multiple document chunks
- **Token Tracking**: Monitors usage
- **Callbacks**: Observability and debugging

## Development

### Run Tests
```bash
python manage.py test
```

### Create Migrations
```bash
python manage.py makemigrations
```

### Django Shell
```bash
python manage.py shell
```

### Admin Interface
Access at http://localhost:8002/admin/

## Docker

Build and run:
```bash
docker build -t summary-service .
docker run -p 8002:8000 --env-file .env summary-service
```

## Production Considerations

1. **Async Processing**: Use Celery for background job processing
2. **Caching**: Cache generated summaries (Redis)
3. **Rate Limiting**: Implement API rate limits
4. **Model Versioning**: Track which model version generated each summary
5. **Cost Monitoring**: Track token usage and costs
6. **Fine-Tuning**: Train custom models for better domain-specific summaries

## Use Cases

This service is designed for summarizing any type of business or technical document:

- **Business Reports**: Quarterly earnings, market analysis, strategic planning documents
- **Research Papers**: Academic research, white papers, technical studies
- **Legal Documents**: Contracts, compliance reports, regulatory filings, case studies
- **Financial Reports**: Budget analyses, investment proposals, audit reports, financial statements
- **Technical Documentation**: API documentation, system specifications, technical designs, architecture reviews
- **Meeting Notes**: Board meetings, project reviews, strategy sessions
- **RFPs/RFIs**: Request for proposals, vendor evaluations, procurement documents
- **General Documents**: Any multi-page document requiring stakeholder-specific summaries

## Who Should Use This

This service is ideal for:

- **Organizations** that need to distribute different views of the same document to different stakeholders
- **Teams** that work with long-form documents requiring quick insights
- **Businesses** that need to synthesize information from multiple sources
- **Professionals** who need to understand key points without reading entire documents
- **Decision-makers** who need executive summaries tailored to their specific concerns

## License

MIT License
